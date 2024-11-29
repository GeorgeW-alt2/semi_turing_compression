#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <thread>
#include <mutex>
#include <future>
#include <functional>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <iterator>
#include <bitset>
#include <cstdint>

// CRC computation helper
uint16_t compute_crc(const std::string& text, uint16_t polynomial = 0x1021, uint16_t init_value = 0x0000) {
    uint16_t crc = init_value;
    for (unsigned char c : text) {
        crc ^= (c << 8);
        for (int i = 0; i < 8; ++i) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ polynomial;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc & 0xFFFF;
}

// Helper to format CRC into a hexadecimal string
std::string format_crc(uint16_t crc) {
    std::ostringstream oss;
    oss << std::uppercase << std::hex << std::setw(4) << std::setfill('0') << crc;
    return oss.str();
}

// Function to check a single candidate in brute force
std::string check_candidate(const std::string& partial_text, const std::string& checksum, uint16_t polynomial, const std::string& candidate) {
    std::string candidate_message = partial_text + candidate;
    uint16_t candidate_crc = compute_crc(candidate_message, polynomial);
    if (format_crc(candidate_crc) == checksum) {
        return candidate_message;
    }
    return "";
}

// Brute force reconstitution
std::string reconstitute_message(const std::string& partial_text, const std::string& checksum, uint16_t polynomial, int missing_length) {
    const std::string charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    std::vector<std::string> candidates;
    std::string result;

    // Generate all combinations of the missing characters
    std::function<void(int, std::string)> generate_combinations;

    generate_combinations = [&](int depth, std::string prefix) {
        if (depth == 0) {
            candidates.push_back(prefix);
            return;
        }
        for (char c : charset) {
            generate_combinations(depth - 1, prefix + c);
        }
};
    generate_combinations(missing_length, "");

    // Use threads for parallel computation
    std::mutex result_mutex;
    std::vector<std::future<std::string>> futures;
    for (const auto& candidate : candidates) {
        futures.emplace_back(std::async(std::launch::async, [&]() {
            return check_candidate(partial_text, checksum, polynomial, candidate);
        }));
    }

    for (auto& future : futures) {
        std::string candidate_result = future.get();
        if (!candidate_result.empty()) {
            std::lock_guard<std::mutex> lock(result_mutex);
            result = candidate_result;
            break;
        }
    }

    return result;
}

int main() {
    // Choose the polynomial
    std::cout << "Choose a standard polynomial:" << std::endl;
    std::cout << "1: CRC-8 (0x07)" << std::endl;
    std::cout << "2: CRC-16 (0x1021)" << std::endl;
    std::cout << "3: CRC-32 (0x04C11DB7)" << std::endl;
    std::cout << "Enter your choice (1, 2, or 3): ";

    int choice;
    std::cin >> choice;

    uint16_t polynomial = 0x1021; // Default to CRC-16
    if (choice == 1) {
        polynomial = 0x07; // CRC-8
    } else if (choice == 3) {
        std::cerr << "CRC-32 is not yet implemented. Defaulting to CRC-16." << std::endl;
    }

    // Read original text
    std::ifstream input_file("test.txt");
    if (!input_file.is_open()) {
        std::cerr << "Failed to open 'test.txt'." << std::endl;
        return 1;
    }
    std::string text((std::istreambuf_iterator<char>(input_file)), std::istreambuf_iterator<char>());
    input_file.close();

    // Compression phase
    int missing_length = 5;
    std::string checksum = format_crc(compute_crc(text, polynomial));
    std::string partial_text = text.substr(0, text.size() - missing_length);

    std::ofstream compressed_file("compressed.tz");
    if (!compressed_file.is_open()) {
        std::cerr << "Failed to write to 'compressed.tz'." << std::endl;
        return 1;
    }
    compressed_file << partial_text + checksum;
    compressed_file.close();

    // Read compressed text
    std::ifstream compressed_input("compressed.tz");
    if (!compressed_input.is_open()) {
        std::cerr << "Failed to open 'compressed.tz'." << std::endl;
        return 1;
    }
    std::string compressed_text((std::istreambuf_iterator<char>(compressed_input)), std::istreambuf_iterator<char>());
    compressed_input.close();

    // Extract partial text and checksum
    partial_text = compressed_text.substr(0, compressed_text.size() - missing_length);
    checksum = compressed_text.substr(compressed_text.size() - missing_length);

    // Reconstitution phase
    std::cout << "Attempting to reconstitute the message from the checksum..." << std::endl;
    std::string reconstructed_message = reconstitute_message(partial_text, checksum, polynomial, missing_length);

    if (!reconstructed_message.empty()) {
        std::cout << "Reconstructed message: " << reconstructed_message << std::endl;
    } else {
        std::cout << "Failed to reconstruct the message." << std::endl;
    }

    // Write reconstructed text
    std::ofstream uncompressed_file("uncompressed.txt");
    if (!uncompressed_file.is_open()) {
        std::cerr << "Failed to write to 'uncompressed.txt'." << std::endl;
        return 1;
    }
    uncompressed_file << (reconstructed_message.empty() ? "Failed to reconstruct." : reconstructed_message);
    uncompressed_file.close();

    return 0;
}
