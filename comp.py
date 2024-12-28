import crcmod
import itertools
import string


class CRCCompressor:
    def __init__(self, polynomial_hex="0x11021", init_value=0x0000):
        self.polynomial_hex = polynomial_hex
        self.init_value = init_value
        self.poly_int = int(polynomial_hex, 16)
        self.crc_func = crcmod.mkCrcFun(self.poly_int, initCrc=init_value, xorOut=0)

    def compute_crc(self, text):
        crc_checksum = self.crc_func(text.encode("utf-8"))
        return f"{crc_checksum:04X}"

    def compress_to_text(self, text, missing_length, layers=3):
        """Compress text and return a plain text format."""
        if len(text) < missing_length * layers:
            raise ValueError(f"Text too short for {layers} layers of compression")

        result = []
        result.append(f"CRCC{layers:02d}{missing_length:02d}{self.polynomial_hex[2:]:>8}")
        current_text = text

        for layer in range(layers):
            original_ending = current_text[-missing_length:]
            checksum = self.compute_crc(current_text)
            result.append(f"L{layer:02d}|{checksum}|{original_ending}")
            current_text = current_text[:-missing_length]

        result.append("TEXT=" + current_text)
        return "\n".join(result)

    def decompress_from_text(self, compressed_text):
        """Decompress from plain text format."""
        lines = compressed_text.strip().split("\n")

        # Parse header
        header = lines[0]
        if not header.startswith("CRCC"):
            raise ValueError("Invalid compression format")

        layers = int(header[4:6])
        missing_length = int(header[6:8])
        poly_hex = "0x" + header[8:].strip()

        if poly_hex != self.polynomial_hex:
            raise ValueError("Polynomial mismatch during decompression")

        # Get compressed text
        text_line = lines[-1]
        if not text_line.startswith("TEXT="):
            raise ValueError("Invalid compression format")
        current_text = text_line[5:]

        # Process layers in reverse
        layer_data = lines[1:-1]
        layer_data.reverse()

        for layer_line in layer_data:
            _, checksum, original_ending = layer_line.split("|")
            reconstructed = self._reconstitute_layer(current_text, checksum, len(original_ending))
            if reconstructed is None:
                raise ValueError("Decompression failed: unable to match CRC")
            current_text = reconstructed

        return current_text

    def _reconstitute_layer(self, partial_text, checksum, missing_length):
        charset = string.printable
        for candidate in itertools.product(charset, repeat=missing_length):
            candidate_ending = "".join(candidate)
            candidate_message = partial_text + candidate_ending
            candidate_crc = self.compute_crc(candidate_message)
            if candidate_crc == checksum:
                return candidate_message
        return None


def main():
    # Create test content
    test_text = "This is a test of our plain text CRC compression format."

    # Initialize compressor with CRC-16
    compressor = CRCCompressor("0x11021")

    # Compress with 2 layers, 1 character per layer
    compressed = compressor.compress_to_text(test_text, missing_length=1, layers=5)

    # Save compressed data
    with open("compressed.txt", "w", encoding="utf-8") as f:
        f.write(compressed)

    print("Compressed data:")
    print("---------------")
    print(compressed)

    # Decompress and verify
    print("\nAttempting decompression...")
    decompressed = compressor.decompress_from_text(compressed)

    if decompressed == test_text:
        print("Successfully reconstructed the original text!")
        print(decompressed)
    else:
        print("Decompression failed!")
        print("Decompressed text:", decompressed)


if __name__ == "__main__":
    main()
