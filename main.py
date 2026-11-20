#!/usr/bin/env python3
"""Sum up 20 November 2026's world news in one image.

A program/v1 entry for make.fun's news-image-20261120 bounty.
Standard library only: this file draws a 1024x1024 newspaper-style
poster with its own tiny 5x7 pixel font and writes it, byte for byte
the same on every run, to /output/entry.png (or to the directory in
MAKEFUN_OUTPUT_DIR when that is set, for local testing).

The stories were reported on 20 November 2026 (see SOURCES.md):
the ICJ's Myanmar genocide ruling, the first Trump-Xi-Putin summit
in Shenzhen, Russia's strikes on Kyiv, the Houthi missile that hit
Riyadh, the AI sell-off around Anthropic's Nasdaq debut, COP31's
weakened draft, Voyager 1 reaching one light-day, Kenya's last
Ebola patient, and GTA 6's record launch.
"""

import os
import struct
import zlib
from binascii import crc32

WIDTH = 1024
HEIGHT = 1024

PAPER = (244, 241, 234)
WHITE = (255, 255, 255)
INK = (20, 32, 43)
GREY = (66, 78, 90)
GOLD = (232, 184, 75)
RED = (192, 57, 43)
BLUE = (36, 86, 166)
ORANGE = (216, 120, 24)
PURPLE = (102, 64, 160)
TEAL = (14, 122, 110)
SPACE = (38, 54, 120)

# A 5x7 pixel font. Each glyph is 7 rows of 5 pixels, "#" is ink.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "$": ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    "%": ["##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
}


class Canvas:
    """A plain RGB pixel buffer with flat drawing helpers."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            at = (y * self.width + x) * 3
            self.pixels[at:at + 3] = bytes(colour)

    def fill_rect(self, x, y, w, h, colour):
        for row in range(y, y + h):
            if 0 <= row < self.height:
                start = max(0, x)
                end = min(self.width, x + w)
                if start < end:
                    at = (row * self.width + start) * 3
                    self.pixels[at:at + (end - start) * 3] = bytes(colour) * (end - start)

    def outline_rect(self, x, y, w, h, colour, thick=3):
        self.fill_rect(x, y, w, thick, colour)
        self.fill_rect(x, y + h - thick, w, thick, colour)
        self.fill_rect(x, y, thick, h, colour)
        self.fill_rect(x + w - thick, y, thick, h, colour)

    def fill_circle(self, cx, cy, radius, colour):
        r2 = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                    self.set_pixel(x, y, colour)

    def text_width(self, text, scale):
        if not text:
            return 0
        return len(text) * 6 * scale - scale

    def draw_text(self, text, x, y, scale, colour):
        cursor = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row_i, row in enumerate(glyph):
                for col_i, mark in enumerate(row):
                    if mark == "#":
                        self.fill_rect(cursor + col_i * scale,
                                       y + row_i * scale, scale, scale, colour)
            cursor += 6 * scale
        return cursor - scale

    def draw_text_centred(self, text, centre_x, y, scale, colour):
        width = self.text_width(text, scale)
        return self.draw_text(text, centre_x - width // 2, y, scale, colour)


def panel(canvas, x, y, w, h, accent, kicker, headline, body):
    """One news panel: white card, accent bar, kicker, headline, body."""
    canvas.fill_rect(x, y, w, h, WHITE)
    canvas.outline_rect(x, y, w, h, INK, 3)
    canvas.fill_rect(x, y, w, 10, accent)
    canvas.draw_text(kicker, x + 22, y + 22, 2, accent)
    line_y = y + 44
    for line in headline:
        canvas.draw_text(line, x + 22, line_y, 4, INK)
        line_y += 36
    line_y = y + 114
    for line in body:
        canvas.draw_text(line, x + 22, line_y, 2, GREY)
        line_y += 19


def draw_poster():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead: a dark band with the day named as large as it can be.
    canvas.fill_rect(0, 0, WIDTH, 124, INK)
    canvas.draw_text_centred("THE WORLD IN ONE DAY", WIDTH // 2, 10, 2, GOLD)
    canvas.draw_text_centred("20 NOVEMBER 2026", WIDTH // 2, 30, 7, WHITE)
    canvas.draw_text_centred("FRIDAY - ONE DAY - ONE IMAGE - THE NEWS THAT MATTERED",
                             WIDTH // 2, 88, 2, GOLD)

    # Hero story: the World Court's first state genocide ruling.
    hx, hy, hw, hh = 16, 136, 992, 140
    canvas.fill_rect(hx, hy, hw, hh, WHITE)
    canvas.outline_rect(hx, hy, hw, hh, INK, 3)
    canvas.fill_rect(hx, hy, hw, 10, RED)
    canvas.fill_circle(hx + 76, hy + 76, 42, RED)
    canvas.draw_text_centred("ICJ", hx + 76, hy + 60, 3, WHITE)
    canvas.draw_text("THE HAGUE - JUSTICE", hx + 148, hy + 20, 2, RED)
    canvas.draw_text("MYANMAR: GENOCIDE", hx + 148, hy + 40, 5, INK)
    canvas.draw_text("WORLD COURT RULES", hx + 148, hy + 82, 5, INK)
    canvas.draw_text("FIRST STATE GENOCIDE RULING - VOTE 9-6 - 1.3M ROHINGYA DISPLACED",
                     hx + 148, hy + 120, 2, GREY)

    # Six panels in two columns and three rows.
    left, right, pw = 16, 520, 488
    rows = [288, 452, 616]
    panel(canvas, left, rows[0], pw, 156, BLUE, "SHENZHEN - DIPLOMACY",
          ["TRUMP XI PUTIN", "HOLD FIRST SUMMIT"],
          ["JOINT PEACE DECLARATION SIGNED",
           "NUCLEAR RISK - UN REFORM - ENERGY"])
    panel(canvas, right, rows[0], pw, 156, RED, "UKRAINE - WAR",
          ["RUSSIA POUNDS KYIV", "8 DEAD - 3 BRIDGES"],
          ["OVERNIGHT MISSILES - 28 INJURED",
           "UKRAINE STRIKES CRIMEA BRIDGE"])
    panel(canvas, left, rows[1], pw, 156, ORANGE, "RIYADH - MIDDLE EAST",
          ["MISSILE DAMAGES", "RIYADH TOWER"],
          ["HOUTHI STRIKE ON PIF TOWER",
           "IRAN WAR MONTH 9 - HORMUZ TANKERS HIT"])
    panel(canvas, right, rows[1], pw, 156, PURPLE, "MARKETS - AI",
          ["STOCKS TUMBLE AS", "AI BOOM IS TESTED"],
          ["ANTHROPIC IPO CLOSES +17%",
           "S+P -2% - NIKKEI -4.8% - GOLD -4.2%"])
    panel(canvas, left, rows[2], pw, 156, TEAL, "ANTALYA - CLIMATE",
          ["COP31 DRAFT DROPS", "FOSSIL FUEL EXIT"],
          ["PHASE-OUT LINE REMOVED FROM DEAL",
           "PACIFIC NATIONS DEMAND MORE"])
    panel(canvas, right, rows[2], pw, 156, SPACE, "SPACE - NASA",
          ["VOYAGER 1 REACHES", "ONE LIGHT-DAY"],
          ["26 BILLION KM FROM EARTH",
           "49 YEARS AFTER 1977 LAUNCH"])

    # Footer: four more of the day's stories in a dark ticker band.
    fy = 784
    canvas.fill_rect(0, fy, WIDTH, HEIGHT - fy, INK)
    canvas.draw_text_centred("ALSO TODAY", WIDTH // 2, fy + 16, 2, GOLD)
    canvas.draw_text_centred("KENYA BEATS EBOLA - LAST PATIENT GOES HOME",
                             WIDTH // 2, fy + 48, 3, WHITE)
    canvas.draw_text_centred("GTA 6 LAUNCH TOPS $2.3 BILLION IN SALES",
                             WIDTH // 2, fy + 88, 3, WHITE)
    canvas.draw_text_centred("UK AND EU SEAL YOUTH MOBILITY DEAL",
                             WIDTH // 2, fy + 128, 3, WHITE)
    canvas.draw_text_centred("US SENATE PASSES ENERGY BILL 62-33",
                             WIDTH // 2, fy + 168, 3, WHITE)
    canvas.draw_text_centred("AS REPORTED ON 20 NOVEMBER 2026 - BBC - REUTERS - AP - UN - NASA",
                             WIDTH // 2, fy + 208, 2, GOLD)
    return canvas


def png_bytes(canvas):
    """Encode the canvas as a PNG with the standard library only."""
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", crc32(kind + data) & 0xFFFFFFFF))

    raw = bytearray()
    stride = canvas.width * 3
    for row in range(canvas.height):
        raw.append(0)  # filter type 0 for every scanline
        start = row * stride
        raw += canvas.pixels[start:start + stride]
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_poster())
    with open(os.path.join(out_dir, "entry.png"), "wb") as handle:
        handle.write(data)
    print(f"wrote entry.png ({len(data)} bytes)")


if __name__ == "__main__":
    main()
