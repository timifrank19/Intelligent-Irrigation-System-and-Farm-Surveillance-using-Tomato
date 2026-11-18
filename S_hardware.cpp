/**
 * INTELLIGENT IRRIGATION SYSTEM - HARDWARE SIMULATOR (Pure C++)
 * 
 * Compile: g++ S_hardware.cpp -o S_hardware.exe -lwinhttp
 * Run:     ./S_hardware.exe
 * 
 * Sends simulated sensor data to backend via HTTP POST
 */

#include <iostream>
#include <iomanip>
#include <cmath>
#include <random>
#include <thread>
#include <chrono>
#include <ctime>
#include <string>
#include <sstream>
#include <windows.h>
#include <winhttp.h>
#include <fstream>

#pragma comment(lib, "winhttp.lib")

using namespace std;

// ============================================
// CONFIGURATION
// ============================================
#define SEND_INTERVAL_MS    15000
#define BACKEND_URL         L"localhost"
#define BACKEND_PORT        8000
#define BACKEND_PATH        L"/api/sensor-data"

#define MORNING_START 5
#define MORNING_END   8
#define EVENING_START 17
#define EVENING_END   20

#define SOIL_MIN 0.20f
#define SOIL_DRY 0.28f
#define SOIL_OPTIMAL 0.35f
#define SOIL_WET 0.42f
#define SOIL_MAX 0.50f
#define TEMP_HIGH 32.0f
#define BATTERY_CRITICAL 20.0f

#define FAULT_BEARING_THRESHOLD     50.0f
#define FAULT_MISALIGNMENT_THRESHOLD 35.0f
#define FAULT_IMBALANCE_THRESHOLD   30.0f
#define FAULT_LOOSENESS_THRESHOLD   30.0f

// ============================================
// GLOBAL VARIABLES
// ============================================
random_device rd;
mt19937 gen(rd());
uniform_real_distribution<> rand_float(-0.02, 0.02);

float soil_moisture = 0.38f;
float temperature = 26.0f;
float humidity = 75.0f;
float vibration = 0.10f;
float battery_percent = 85.0f;
float battery_voltage = 12.5f;

bool soil_sensor_failed = false;
bool temp_sensor_failed = false;
bool vibration_sensor_failed = false;

bool pump_status = false;
bool manual_override = false;
int virtual_hour = 0;
int virtual_day = 1;

float soil_dry_threshold = SOIL_DRY;
float temp_high_threshold = TEMP_HIGH;
string vibration_fault = "Normal";
float vibration_dominant_freq = 0.0f;

ofstream log_file;

// ============================================
// HTTP POST
// ============================================
bool sendHttpPost(const string& json_data) {
    HINTERNET hSession = WinHttpOpen(L"SensorSimulator/1.0", 
                                      WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                      WINHTTP_NO_PROXY_NAME, 
                                      WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) return false;
    
    HINTERNET hConnect = WinHttpConnect(hSession, BACKEND_URL, BACKEND_PORT, 0);
    if (!hConnect) { WinHttpCloseHandle(hSession); return false; }
    
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"POST", BACKEND_PATH,
                                            NULL, NULL, NULL, 0);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return false;
    }
    
    LPCWSTR headers = L"Content-Type: application/json\r\n";
    WinHttpSendRequest(hRequest, headers, wcslen(headers),
                       (LPVOID)json_data.c_str(), json_data.length(), json_data.length(), 0);
    WinHttpReceiveResponse(hRequest, NULL);
    
    DWORD statusCode = 0;
    DWORD dwSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                        NULL, &statusCode, &dwSize, NULL);
    
    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);
    
    return (statusCode == 200);
}

// ============================================
// FAULT-TOLERANT LAYER: NN + Fuzzy
// ============================================
float predictSoilFromTemperature(float temp, float hour) {
    float w1 = -0.015f, w2 = 0.008f, bias = 0.42f;
    float linear = w1 * temp + w2 * hour + bias;
    float sigmoid = 1.0f / (1.0f + exp(-linear));
    return 0.2f + sigmoid * 0.3f;
}

bool fuzzyIrrigationDecision(float soil, float temp, float confidence, float& out_conf) {
    float soil_dry_score = (soil < 0.30f) ? 1.0f : (soil > 0.35f ? 0.0f : (0.35f - soil) / 0.05f);
    float temp_high_score = (temp > 32.0f) ? 1.0f : (temp < 28.0f ? 0.0f : (temp - 28.0f) / 4.0f);
    float rule1 = soil_dry_score * temp_high_score * (confidence / 100.0f);
    float rule2 = soil_dry_score * (confidence / 100.0f) * 0.8f;
    float soil_wet_score = (soil > 0.42f) ? 1.0f : (soil < 0.35f ? 0.0f : (soil - 0.35f) / 0.07f);
    float rule3 = soil_wet_score * (confidence / 100.0f);
    
    float pump_on_score = max(rule1, rule2);
    float pump_off_score = rule3;
    out_conf = max(pump_on_score, pump_off_score) * 100.0f;
    return pump_on_score > pump_off_score;
}

bool makeFaultTolerantDecision(float raw_soil, float temp, bool soil_failed, bool temp_failed, float& out_confidence) {
    float reliable_soil = soil_failed ? predictSoilFromTemperature(temp, virtual_hour) : raw_soil;
    float reliable_temp = temp_failed ? (28.0f + (0.35f - reliable_soil) * 15.0f) : temp;
    
    float confidence = 100.0f;
    if (soil_failed) confidence -= 30.0f;
    if (temp_failed) confidence -= 30.0f;
    confidence = max(confidence, 40.0f);
    out_confidence = confidence;
    
    float conf;
    return fuzzyIrrigationDecision(reliable_soil, reliable_temp, confidence, conf);
}

// ============================================
// FFT VIBRATION FAULT DETECTION
// ============================================
string runFFTAndGetFault(float vibration_value) {
    float random_factor = (rand() % 100) / 100.0f;
    
    if (vibration_value > 0.45f && random_factor > 0.7f) return "Bearing Wear";
    if (vibration_value > 0.35f && random_factor > 0.5f) return "Misalignment";
    if (vibration_value > 0.30f && random_factor > 0.3f) return "Imbalance";
    if (vibration_value > 0.40f && random_factor > 0.2f) return "Looseness";
    if (vibration_value > 0.25f && random_factor < 0.2f) return "Cavitation";
    return "Normal";
}

// ============================================
// HELPERS
// ============================================
bool isSmartScheduleTime(int hour) {
    return (hour >= MORNING_START && hour <= MORNING_END) ||
           (hour >= EVENING_START && hour <= EVENING_END);
}

string getCurrentTimestamp() {
    time_t now = time(nullptr);
    char buf[64];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", localtime(&now));
    return string(buf);
}

// ============================================
// SENSOR SIMULATION
// ============================================
void simulateSensorFailures() {
    if (rand() % 1000 < 10 && !soil_sensor_failed && !temp_sensor_failed && !vibration_sensor_failed) {
        int failed = rand() % 3;
        if (failed == 0) { soil_sensor_failed = true; cout << "⚠️ SOIL SENSOR FAILURE! Using NN prediction." << endl; }
        else if (failed == 1) { temp_sensor_failed = true; cout << "⚠️ TEMP SENSOR FAILURE! Using NN prediction." << endl; }
        else { vibration_sensor_failed = true; cout << "⚠️ VIBRATION SENSOR FAILURE!" << endl; }
    }
}

void simulateSensors() {
    static int gen_count = 0;
    gen_count++;
    virtual_hour = (virtual_hour + 1) % 24;
    if (virtual_hour == 0) virtual_day++;
    
    simulateSensorFailures();
    
    // Soil moisture
    float change = (virtual_hour >= 8 && virtual_hour <= 18) ? -0.015f : 0.005f;
    if (temperature > 32) change -= 0.005f;
    if (temperature < 24) change += 0.003f;
    if (pump_status) change += 0.040f;
    soil_moisture += change + rand_float(gen) * 0.005f;
    soil_moisture = max(SOIL_MIN, min(SOIL_MAX, soil_moisture));
    
    // Temperature
    float temp_peak = 33.0f, temp_low = 23.0f;
    float temp_cycle = cos((virtual_hour - 14) * 2 * 3.14159f / 24) * ((temp_peak - temp_low) / 2);
    temperature = temp_low + (temp_peak - temp_low) / 2 + temp_cycle + rand_float(gen);
    temperature = max(20.0f, min(36.0f, temperature));
    
    // Humidity
    humidity = 80.0f - (temperature - 22.0f) * 1.5f + rand_float(gen) * 3;
    humidity = max(45.0f, min(95.0f, humidity));
    
    // Vibration
    if (pump_status && (rand() % 100) < 2) vibration = 0.55f + (rand() % 40) / 100.0f;
    else if (pump_status) vibration = 0.12f + (rand() % 8) / 100.0f;
    else vibration = 0.07f + (rand() % 5) / 100.0f;
    if ((rand() % 200) < 1 && !pump_status) vibration = 0.60f + (rand() % 20) / 100.0f;
    
    // Battery
    battery_percent += (virtual_hour >= 8 && virtual_hour <= 16) ? 0.2f : -0.1f;
    battery_percent = max(10.0f, min(100.0f, battery_percent));
    battery_voltage = 11.0f + (battery_percent / 100.0f) * 2.5f;
    
    // FFT
    vibration_fault = runFFTAndGetFault(vibration);
    vibration_dominant_freq = 25.0f + (rand() % 20);
    
    // Decision
    if (manual_override) { pump_status = true; return; }
    if (battery_percent < BATTERY_CRITICAL) { pump_status = false; return; }
    
    if (soil_sensor_failed || temp_sensor_failed) {
        float conf;
        pump_status = makeFaultTolerantDecision(soil_moisture, temperature, soil_sensor_failed, temp_sensor_failed, conf);
        if (soil_sensor_failed || temp_sensor_failed) {
            cout << "🔄 Using Fault-Tolerant Mode (NN + Fuzzy)" << endl;
        }
        return;
    }
    
    bool isSchedule = isSmartScheduleTime(virtual_hour);
    if (isSchedule && soil_moisture < SOIL_WET) pump_status = true;
    else if (temperature > temp_high_threshold) pump_status = true;
    else if (soil_moisture < soil_dry_threshold) pump_status = true;
    else if (soil_moisture < SOIL_MIN + 0.03) pump_status = true;
    else if (soil_moisture > SOIL_WET && temperature < temp_high_threshold - 2) pump_status = false;
    else if (soil_moisture > SOIL_OPTIMAL && !isSchedule && temperature < temp_high_threshold - 2) pump_status = false;
    else if ((virtual_hour < 5 || virtual_hour > 21) && soil_moisture > SOIL_DRY && temperature < temp_high_threshold - 3) pump_status = false;
    else pump_status = false;
}

// ============================================
// SEND DATA
// ============================================
string getDecisionReason() {
    if (manual_override) return "Manual override";
    if (battery_percent < BATTERY_CRITICAL) return "Low battery";
    if (soil_sensor_failed || temp_sensor_failed) return "Fault-Tolerant Mode (NN + Fuzzy)";
    
    bool isSchedule = isSmartScheduleTime(virtual_hour);
    if (isSchedule && soil_moisture < SOIL_WET) return "Smart schedule";
    if (temperature > temp_high_threshold) return "High temperature";
    if (soil_moisture < soil_dry_threshold) return "Low soil moisture";
    if (soil_moisture < SOIL_MIN + 0.03) return "Very dry soil";
    if (soil_moisture > SOIL_WET) return "Soil wet";
    if (soil_moisture > SOIL_OPTIMAL) return "Soil optimal";
    if (virtual_hour < 5 || virtual_hour > 21) return "Night time";
    return "Normal";
}

void sendToBackend() {
    string reason = getDecisionReason();
    
    stringstream json;
    json << "{";
    json << "\"soil_moisture\":" << fixed << setprecision(3) << soil_moisture << ",";
    json << "\"temperature\":" << fixed << setprecision(2) << temperature << ",";
    json << "\"humidity\":" << fixed << setprecision(1) << humidity << ",";
    json << "\"vibration\":" << fixed << setprecision(3) << vibration << ",";
    json << "\"battery\":" << fixed << setprecision(1) << battery_voltage << ",";
    json << "\"battery_percentage\":" << fixed << setprecision(1) << battery_percent << ",";
    json << "\"pump_decision\":" << (pump_status ? 1 : 0) << ",";
    json << "\"decision_reason\":\"" << reason << "\",";
    json << "\"soil_sensor_failed\":" << (soil_sensor_failed ? 1 : 0) << ",";
    json << "\"temp_sensor_failed\":" << (temp_sensor_failed ? 1 : 0) << ",";
    json << "\"vibration_sensor_failed\":" << (vibration_sensor_failed ? 1 : 0) << ",";
    json << "\"vibration_fault\":\"" << vibration_fault << "\",";
    json << "\"vibration_dominant_freq\":" << fixed << setprecision(1) << vibration_dominant_freq;
    json << "}";
    
    bool sent = sendHttpPost(json.str());
    
    string scheduleIcon = isSmartScheduleTime(virtual_hour) ? "[SCHEDULE]" : "          ";
    string pumpIcon = pump_status ? "PUMP=ON " : "PUMP=OFF";
    string statusIcon = sent ? "✅" : "❌";
    string faultIcon = (vibration_fault != "Normal") ? " 🔴" : "";
    
    string sensorStatus = "";
    if (soil_sensor_failed) sensorStatus += " [SOIL FAIL]";
    if (temp_sensor_failed) sensorStatus += " [TEMP FAIL]";
    if (vibration_sensor_failed) sensorStatus += " [VIB FAIL]";
    
    cout << statusIcon << " " << scheduleIcon << " ";
    cout << "[Day " << virtual_day << " | " << setw(2) << setfill('0') << virtual_hour << ":00] ";
    cout << "Soil=" << fixed << setprecision(3) << soil_moisture << " ";
    cout << "Temp=" << fixed << setprecision(2) << temperature << "C ";
    cout << "Hum=" << setprecision(0) << humidity << "% ";
    cout << "Vib=" << setprecision(3) << vibration << "g ";
    cout << "Batt=" << setprecision(0) << battery_percent << "%  ";
    cout << pumpIcon << sensorStatus << faultIcon;
    cout << " | " << reason;
    if (vibration_fault != "Normal") cout << " ⚠️ " << vibration_fault;
    cout << endl;
    
    if (log_file.is_open()) {
        log_file << getCurrentTimestamp() << ","
                 << fixed << setprecision(3) << soil_moisture << ","
                 << fixed << setprecision(2) << temperature << ","
                 << fixed << setprecision(1) << humidity << ","
                 << fixed << setprecision(3) << vibration << ","
                 << fixed << setprecision(1) << battery_percent << ","
                 << (pump_status ? 1 : 0) << ","
                 << reason << ","
                 << vibration_fault << "\n";
        log_file.flush();
    }
}

// ============================================
// MAIN
// ============================================
int main() {
    cout << "\n" << string(70, '=') << "\n";
    cout << "     INTELLIGENT IRRIGATION SYSTEM - SIMULATOR\n";
    cout << string(70, '=') << "\n";
    cout << "     📊 FFT Vibration Fault Detection: ENABLED\n";
    cout << "     🧠 Neural Network (Fault-Tolerant): ENABLED\n";
    cout << "     🔄 Fuzzy Logic (Fault-Tolerant): ENABLED\n";
    cout << "     ⚡ Conflict Resolution: Hardware wins\n";
    cout << string(70, '=') << "\n\n";
    cout << "     Sending data to: http://localhost:8000/api/sensor-data\n";
    cout << "     Press Ctrl+C to stop\n\n";
    
    log_file.open("simulator_log.csv");
    if (log_file.is_open()) {
        log_file << "timestamp,soil,temp,humidity,vibration,battery,pump,reason,vibration_fault\n";
        cout << "📁 Logging to simulator_log.csv\n";
    }
    
    cout << "\n🚀 SIMULATION STARTED!\n" << endl;
    
    while (true) {
        auto start = chrono::steady_clock::now();
        simulateSensors();
        sendToBackend();
        
        auto elapsed = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start).count();
        if (elapsed < SEND_INTERVAL_MS) {
            this_thread::sleep_for(chrono::milliseconds(SEND_INTERVAL_MS - elapsed));
        }
    }
    
    return 0;
}