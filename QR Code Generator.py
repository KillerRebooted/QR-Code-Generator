import customtkinter as ctk
import time

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

# Convery List to Visible QR Code
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

def convert_to_encoded_data(link):

    binary_string = ""

    for char in link:
        binary_string += f"{ord(char):08b}"

    return binary_string

# Version 2 QR Code Generator
def version2(link, color_reversed):
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
    numeric = "0001"
    alphanumeric = "0010"
    binary = "0100"

    if link.isdigit():
        type = numeric
    elif link.isalnum():
        type = alphanumeric
    else:
        type = binary
    
    bits = data_to_qrcode(bits, row_size, type)

    # Specify Length

    length = f"{len(link):08b}"
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

    data = convert_to_encoded_data(link)
    bits = data_to_qrcode(bits, row_size, data)

    # Add 4 Blank Bits to represent end of Message/Link

    data = "0000"
    bits = data_to_qrcode(bits, row_size, data)

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