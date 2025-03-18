import customtkinter as ctk
import reedsolo

win = ctk.CTk()
win.title("QR Code Generator")

# 0 -> Light
# 1 -> Dark

#Convert given Row, Column to Index of the List
def rc_to_index(r, c, row_size):

    index = 0

    index += (r-1)*row_size
    index += c-1

    return index

# Convert List to Visible QR Code
def update_qrcode(bits, bit_boxes, color_reversed):

    if not color_reversed:
        color_for_0 = "white"
        color_for_1 = "black"
    else:
        color_for_0 = "black"
        color_for_1 = "white"

    for bit, bit_box in zip(bits, bit_boxes):
        if bit == 0:
            bit_box.configure(fg_color=color_for_0, hover_color=color_for_0)
        if bit == 1:
            bit_box.configure(fg_color=color_for_1, hover_color=color_for_1)

# Update list of bits to match their indices on the QR Code
def data_to_qrcode(bits, row_size, data):

    r, c = row_size, row_size

    # Initial Variable to Determine whether encoding is upwards or downwards to determine encoding pattern 
    upwards = True

    zigzag = 0
    for bit in data:
        
        # To look for an empty box and keep looking till found to encode data into it while avoiding encoded and reserved boxes
        found_empty = False

        while not found_empty:

            if (r, c) not in modified_boxes:

                bits[rc_to_index(r, c, row_size)] = int(bit)
                found_empty = True
            
                modified_boxes.add((r, c))

            if zigzag == 0:
                c -= 1
                zigzag += 1

            elif (upwards) and (zigzag == 1):
                r -= 1
                c += 1
                zigzag -= 1

            elif (not upwards) and (zigzag == 1):
                
                r += 1
                c += 1
                zigzag -= 1

            
            if r < 1:
                r = 1
                c -= 2
                upwards = False
            
            if r > row_size:
                r = row_size
                c -= 2
                upwards = True
        
    return bits

# Convert given data to Integer and Binary Format
def convert_to_encoded_data(link):

    integer_list = []
    binary_string = ""

    for char in link:
        integer_list.append(ord(char))
        binary_string += f"{ord(char):08b}"

    return integer_list, binary_string

# Get Data Length to get best ECC Length for given data
def get_data_length(data, mode):
    if mode == "numeric":
        num_digits = len(data)
        return (num_digits // 3) * 10 + (7 if num_digits % 3 == 2 else 4 if num_digits % 3 == 1 else 0)
    
    elif mode == "alphanumeric":
        num_chars = len(data)
        return (num_chars // 2) * 11 + (6 if num_chars % 2 == 1 else 0)
    
    elif mode == "binary":
        return len(data) * 8  # Each character = 8 bits
    
    elif mode == "kanji":
        return len(data) * 13  # Each Kanji character = 13 bits

    else:
        raise ValueError("Invalid mode! Choose from 'numeric', 'alphanumeric', 'binary', or 'kanji'.")

def get_appropriate_ecc_level(version, mode, data_length):
    """
    Determines the bit length of the given data based on QR mode and version,
    then selects the most suitable error correction level.
    """

    # QR Code Capacity Table: {version: {mode: {ecc_level: max_bits}}}
    qr_capacity = {
    1: {
        "numeric": {"L": 152, "M": 128, "Q": 104, "H": 72},
        "alphanumeric": {"L": 132, "M": 108, "Q": 86, "H": 62},
        "binary": {"L": 104, "M": 88, "Q": 64, "H": 48},
        "kanji": {"L": 78, "M": 66, "Q": 50, "H": 36}
        },
    2: {
        "numeric": {"L": 272, "M": 224, "Q": 176, "H": 128},
        "alphanumeric": {"L": 224, "M": 184, "Q": 144, "H": 104},
        "binary": {"L": 192, "M": 224, "Q": 144, "H": 104},  # **Corrected**
        "kanji": {"L": 144, "M": 128, "Q": 100, "H": 72}
        },
    3: {
        "numeric": {"L": 440, "M": 368, "Q": 288, "H": 208},
        "alphanumeric": {"L": 360, "M": 312, "Q": 240, "H": 172},
        "binary": {"L": 288, "M": 256, "Q": 192, "H": 144},  # **Fixed**
        "kanji": {"L": 216, "M": 176, "Q": 132, "H": 104}
        },
    4: {
        "numeric": {"L": 640, "M": 512, "Q": 384, "H": 288},
        "alphanumeric": {"L": 520, "M": 416, "Q": 312, "H": 236},
        "binary": {"L": 384, "M": 328, "Q": 256, "H": 192},
        "kanji": {"L": 288, "M": 256, "Q": 186, "H": 144}
        },
    5: {
        "numeric": {"L": 864, "M": 688, "Q": 496, "H": 368},
        "alphanumeric": {"L": 696, "M": 552, "Q": 400, "H": 280},
        "binary": {"L": 496, "M": 416, "Q": 312, "H": 224},
        "kanji": {"L": 368, "M": 312, "Q": 234, "H": 168}
        }
    }

    # Select the best ECC level that fits the data
    for ecc_level in ["H", "Q", "M", "L"]:  # Prioritize stronger ECC first
        if data_length <= qr_capacity[version][mode][ecc_level]:
            return data_length, ecc_level

    # If no ECC level fits, return None (data too long for this version)
    return data_length, None

# Get appropriate Error Correction Length
def get_ecc_length(qr_version, ecc_level):
    """
    Returns the ECC length for a given QR version and error correction level.

    :param qr_version: int (1-40) - QR Code version
    :param ecc_level: str ('L', 'M', 'Q', 'H') - Error correction level
    :return: int - Number of ECC codewords
    """

    QR_ECC_TABLE = {
    1:  {"L": 7, "M": 10, "Q": 13, "H": 17},
    2:  {"L": 10, "M": 16, "Q": 22, "H": 28},
    3:  {"L": 15, "M": 26, "Q": 36, "H": 44},
    4:  {"L": 20, "M": 36, "Q": 52, "H": 64},
    5:  {"L": 26, "M": 48, "Q": 72, "H": 88},
    6:  {"L": 36, "M": 64, "Q": 96, "H": 112},
    7:  {"L": 40, "M": 72, "Q": 108, "H": 130},
    8:  {"L": 48, "M": 88, "Q": 132, "H": 156},
    9:  {"L": 60, "M": 110, "Q": 160, "H": 192},
    10: {"L": 72, "M": 130, "Q": 192, "H": 224},
    11: {"L": 80, "M": 150, "Q": 224, "H": 264},
    12: {"L": 96, "M": 176, "Q": 260, "H": 308},
    13: {"L": 104, "M": 198, "Q": 288, "H": 352},
    14: {"L": 120, "M": 216, "Q": 320, "H": 384},
    15: {"L": 132, "M": 240, "Q": 360, "H": 432},
    16: {"L": 144, "M": 280, "Q": 408, "H": 480},
    17: {"L": 168, "M": 308, "Q": 448, "H": 532},
    18: {"L": 180, "M": 338, "Q": 504, "H": 588},
    19: {"L": 196, "M": 364, "Q": 546, "H": 650},
    20: {"L": 224, "M": 416, "Q": 600, "H": 700},
    21: {"L": 224, "M": 442, "Q": 644, "H": 750},
    22: {"L": 252, "M": 476, "Q": 690, "H": 816},
    23: {"L": 270, "M": 504, "Q": 750, "H": 900},
    24: {"L": 300, "M": 560, "Q": 810, "H": 960},
    25: {"L": 312, "M": 588, "Q": 870, "H": 1050},
    26: {"L": 336, "M": 644, "Q": 952, "H": 1110},
    27: {"L": 360, "M": 700, "Q": 1020, "H": 1200},
    28: {"L": 390, "M": 728, "Q": 1050, "H": 1260},
    29: {"L": 420, "M": 784, "Q": 1140, "H": 1350},
    30: {"L": 450, "M": 812, "Q": 1200, "H": 1440},
    31: {"L": 480, "M": 868, "Q": 1290, "H": 1530},
    32: {"L": 510, "M": 924, "Q": 1350, "H": 1620},
    33: {"L": 540, "M": 980, "Q": 1440, "H": 1710},
    34: {"L": 570, "M": 1036, "Q": 1530, "H": 1800},
    35: {"L": 570, "M": 1064, "Q": 1590, "H": 1890},
    36: {"L": 600, "M": 1120, "Q": 1680, "H": 1980},
    37: {"L": 630, "M": 1204, "Q": 1770, "H": 2100},
    38: {"L": 660, "M": 1260, "Q": 1860, "H": 2220},
    39: {"L": 720, "M": 1316, "Q": 1950, "H": 2310},
    40: {"L": 750, "M": 1372, "Q": 2040, "H": 2430},
    }

    if (qr_version in QR_ECC_TABLE) and (ecc_level in QR_ECC_TABLE[qr_version]):
        return QR_ECC_TABLE[qr_version][ecc_level]
    else:
        raise ValueError("Invalid QR version or ECC level")

# Version 2 QR Code Generator
def version2(data, ecc_level=None, color_reversed=False):
    global modified_boxes

    modified_boxes = set()
    
    row_size = 25

    bits = [0]*(row_size**2)
    bit_boxes = [ctk.CTkButton(win, text="", height=30, width=30, border_color="black", border_width=grid, corner_radius=0) for button in range(row_size**2)]

    #Place Bit Boxes
    r, c = 1, 1
    for bit_box in bit_boxes:
        
        bit_box.grid(row=r, column=c)

        c += 1

        if c == row_size+1:
            r += 1
            c = 1

    # Alignment Patterns

    locator1 = [(1, 7), (1, 7)]
    locator2 = [(1, 7), (row_size-6, 25)]
    locator3 = [(row_size-6, 25), (1, 7)]

    locators = [locator1, locator2, locator3]

    for locator in locators:

        for r in range(locator[0][0], locator[0][1]+1):
            for c in range(locator[1][0], locator[1][1]+1):

                modified_boxes.add((r, c))
                
                if ((r-locator[0][0]) in [1, 5] and ((c-locator[1][0]) not in [0, 6])) or ((c-locator[1][0]) in [1, 5] and ((r-locator[0][0]) not in [0, 6])):
                    continue
                
                bits[rc_to_index(r, c, row_size)] = 1

    locator4 = [(row_size-8, row_size-4), (row_size-8, row_size-4)]
    locator = locator4
    for r in range(locator[0][0], locator[0][1]+1):
        for c in range(locator[1][0], locator[1][1]+1):

            modified_boxes.add((r, c))

            if ((r-locator[0][0]) in [1, 3] and ((c-locator[1][0]) not in [0, 4])) or ((c-locator[1][0]) in [1, 3] and ((r-locator[0][0]) not in [0, 4])):
                continue
                
            bits[rc_to_index(r, c, row_size)] = 1

    locator5 = (9, row_size-8)
    locator = locator5
    for r in range(locator[0], locator[1]+1):
        modified_boxes.add((r, c))

        c = 7
        if (r-9)%2 == 0:
            bits[rc_to_index(r, c, row_size)] = 1
    for c in range(locator[0], locator[1]+1):
        modified_boxes.add((r, c))

        r = 7
        if (c-9)%2 == 0:
            bits[rc_to_index(r, c, row_size)] = 1

    # Useless Pixel
    modified_boxes.add((row_size-7, 9, row_size))
    bits[rc_to_index(row_size-7, 9, row_size)] = 1

    # Set Encoding
    numeric = ("0001", "numeric")
    alphanumeric = ("0010", "alphanumeric")
    binary = ("0100", "binary")

    if data.isdigit():
        type = numeric
    elif data.isalnum():
        type = alphanumeric
    else:
        type = binary
    
    bits = data_to_qrcode(bits, row_size, type[0])

    # Specify Length

    length = f"{len(data):08b}"
    bits = data_to_qrcode(bits, row_size, length)
    
    # Reserved Space for Format Strips

    for r in range(1, 9+1):
        for c in range(1, 9+1):
            modified_boxes.add((r, c))
        for c in range(row_size-7, row_size+1):
            modified_boxes.add((r, c))

    for r in range(row_size-7, row_size+1):
        for c in range(1, 9+1):
            modified_boxes.add((r, c))

    # Encode Data

    integer_data, binary_data = convert_to_encoded_data(data)
    bits = data_to_qrcode(bits, row_size, binary_data)

    # Add 4 Blank Bits to represent end of Message/Link

    padding_data = "0000"
    bits = data_to_qrcode(bits, row_size, padding_data)

    # Add Error Correction Bits to the encoded data

    # Get appropriate ECC Length
    data_size = get_data_length(data, type[1])
    if ecc_level == None:
        ecc_level = get_appropriate_ecc_level(2, type[1], data_size)[1]
        if ecc_level == None:
            raise ValueError("Inappropriate QR Version for data of this length.")
    ecc_length = get_ecc_length(2, ecc_level)
    
    # Initialize Reed-Solomon codec
    rs = reedsolo.RSCodec(ecc_length)

    # Encode the message using Reed-Solomon
    encoded_data = rs.encode(bytes(integer_data))

    # Extract only the last 16 bytes (ECC bytes)
    ecc_bytes = encoded_data[-ecc_length:]
    binary_data = "".join(f"{x:08b}" for x in ecc_bytes)

    bits = data_to_qrcode(bits, row_size, binary_data)

    update_qrcode(bits, bit_boxes, color_reversed)

    """for x in modified_boxes:
        for box in bit_boxes:
            if (box.grid_info()["row"], box.grid_info()["column"]) == x:
                box.configure(hover_color="cyan")"""

def main():

    link = "www.youtube.com/veritasium"

    version2(link, color_reversed=False)

    win.mainloop()

if __name__ == "__main__":
    grid = True
    main()