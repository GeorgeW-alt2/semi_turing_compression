import crcmod
import itertools
import string

missing_length = 5 # The length of missing characters to brute force

def compute_crc(text, polynomial_hex="0x11021", init_value=0x0000):
    """
    Computes the CRC checksum for a given text using crcmod with standard polynomials.
    """
    poly_int = int(polynomial_hex, 16)
    crc_func = crcmod.mkCrcFun(poly_int, initCrc=init_value, xorOut=0)
    crc_checksum = crc_func(text.encode('utf-8'))
    return f"{crc_checksum:04X}"


def reconstitute_message(partial_text, checksum, polynomial_hex, missing_length):
    """
    Attempts to reconstitute the original message from the CRC checksum using brute force.
    Note: This is computationally intensive and may not always be successful.
    
    Parameters:
    - partial_text: The partially known message (string).
    - checksum: The target CRC checksum (hex string).
    - polynomial_hex: The polynomial used for CRC computation (hex string).
    - missing_length: The maximum length of the missing portion to brute force.
    
    Returns:
    - The reconstructed message if found, otherwise None.
    """
    poly_int = int(polynomial_hex, 16)
    crc_func = crcmod.mkCrcFun(poly_int, initCrc=0, xorOut=0)
    candidate_message = ""
    charset = string.ascii_letters + string.digits
    for candidate in itertools.product(charset, repeat=missing_length):
        candidate_message = partial_text + ''.join(candidate)
        candidate_crc = f"{crc_func(candidate_message.encode('utf-8')):04X}"
        if candidate_crc == checksum:
            return candidate_message
    return candidate_message


def main():
    print("Choose a standard polynomial:")
    print("1: CRC-8 (0x107)")
    print("2: CRC-16 (0x11021)")
    print("3: CRC-32 (0x104C11DB7)")
    choice = input("Enter your choice (1, 2, or 3): ")

    # Choose the appropriate polynomial
    if choice == "1":
        polynomial = "0x107"  # CRC-8
    elif choice == "2":
        polynomial = "0x11021"  # CRC-16
    elif choice == "3":
        polynomial = "0x104C11DB7"  # CRC-32
    else:
        print("Invalid choice. Using default CRC-16.")
        polynomial = "0x11021"
    
    # Read the original text from file
    with open("test.txt", encoding="utf-8") as f:
        text = f.read()
    # Compression phase: Calculate the CRC and "compress" the text by removing the missing length portion
    checksum = ""
    compression = ""
    for i in range(1):
        checksum = compute_crc(text, polynomial)
        text = text[:-missing_length]  # Remove the last 'missing_length' characters
        text += compute_crc(text + checksum, polynomial)
    
    # Write the compressed text to a file
    with open("compressed.tz", "w", encoding="utf-8") as f:
        f.write(text)
        
    # Read the compressed text from the file for reconstitution
    with open("compressed.tz", encoding="utf-8") as f:
        text = f.read()
    reconstructed_message = text
    # Reconstitution phase: Brute force missing portion of the text
    for i in range(1):
        checksum = reconstructed_message[:-4]
        print(len(checksum))
        reconstructed_message = reconstitute_message(reconstructed_message, checksum, polynomial, missing_length)
   
    # Write the reconstituted text to a file
    with open("uncompressed.txt", "w", encoding="utf-8") as f:
        f.write(text)
        
    checksum = compute_crc(reconstructed_message, polynomial)

    # Attempt semi brute force reconstruction
    print("Attempting to reconstitute the message from the checksum...")

if __name__ == "__main__":
    main()
