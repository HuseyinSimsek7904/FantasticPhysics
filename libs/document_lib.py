import json

from libs import options_lib
import pygame


class DocumentViewer:
    def __init__(self, color, background_color):
        self.color = color
        self.background_color = background_color
        self.escapes = {}

    def merge_horizontal(self, left, right, size, offset=0):
        surface = pygame.Surface(
            (left.get_width() + right.get_width() + int(offset * size), max(left.get_height(), right.get_height())))
        surface.fill(self.background_color)

        left_rect = left.get_rect()
        right_rect = right.get_rect()

        left_rect.midleft = 0, surface.get_height() // 2
        right_rect.midright = surface.get_width(), surface.get_height() // 2

        surface.blit(left, left_rect)
        surface.blit(right, right_rect)

        return surface

    def merge_vertical(self, top, bottom, size, offset=0):
        surface = pygame.Surface(
            (max(top.get_width(), bottom.get_width()), top.get_height() + bottom.get_height() + int(offset * size)))
        surface.fill(self.background_color)

        top_rect = top.get_rect()
        bottom_rect = bottom.get_rect()

        top_rect.midtop = surface.get_width() // 2, 0
        bottom_rect.midtop = surface.get_width() // 2, top_rect.bottom + offset

        surface.blit(top, top_rect)
        surface.blit(bottom, bottom_rect)

        return surface

    def merge_vertical_with_line(self, top, bottom, size, line_width, offset=0):
        surface = self.merge_vertical(top, bottom, size, line_width + offset)
        pygame.draw.line(surface, self.color,
                         (0, top.get_height()),
                         (surface.get_width(), top.get_height()), int(size * line_width))

        return surface

    def list_vertical(self, top, bottom, size, offset=0, bottom_offset=0):
        surface = pygame.Surface((max(top.get_width(), bottom.get_width()) + int(bottom_offset * size),
                                  top.get_height() + bottom.get_height() + int(offset * size)))
        surface.fill(self.background_color)

        top_rect = top.get_rect()
        bottom_rect = bottom.get_rect()

        top_rect.topleft = 0, 0
        bottom_rect.topleft = int(bottom_offset * size), top_rect.bottom + int(offset * size)

        surface.blit(top, top_rect)
        surface.blit(bottom, bottom_rect)

        return surface

    def list_vertical_with_line(self, top, bottom, size, line_width, offset=0, bottom_offset=0):
        top_rect = top.get_rect()
        surface = self.list_vertical(top, bottom, size, line_width + offset, bottom_offset)
        pygame.draw.line(surface, self.color, top_rect.bottomleft, top_rect.bottomright, int(size * line_width))

        return surface

    def merges_horizontal(self, *items):
        width = 0
        height = 0

        for item in items:
            width += item.get_width()
            height = max(height, item.get_height())

        surface = pygame.Surface((width, height))
        surface.fill(self.background_color)

        mid_right = 0, surface.get_height() // 2

        for item in items:
            rect = item.get_rect()
            rect.midleft = mid_right
            surface.blit(item, rect)
            mid_right = rect.midright

        return surface

    def merges_vertical(self, *items):
        width = 0
        height = 0

        for item in items:
            width = max(width, item.get_width())
            height += item.get_height()

        surface = pygame.Surface((width, height))
        surface.fill(self.background_color)

        mid_top = 0, surface.get_height() // 2

        for item in items:
            rect = item.get_rect()
            rect.midtop = mid_top
            surface.blit(item, rect)
            mid_top = (rect.midbottom.x, rect.midbottom.y)

        return surface

    def merge_power_index(self, base, power, index):
        base_rect = base.get_rect()

        if power is None:
            power_width = 0
            power_height = base_rect.height / 2

        else:
            power_rect = power.get_rect()
            power_width = power_rect.width
            power_height = power_rect.height

        if index is None:
            index_width = 0
            index_height = base_rect.height / 2

        else:
            index_rect = index.get_rect()
            index_width = index_rect.width
            index_height = index_rect.height

        surface = pygame.Surface(
            (base_rect.width + int(max(power_width, index_width)), int(power_height + index_height)))
        surface.fill(self.background_color)

        base_rect.topleft = 0, int(power_width)
        surface.blit(base, base_rect)

        if power is not None:
            power_rect.bottomleft = base_rect.midright
            surface.blit(power, power_rect)

        if index is not None:
            index_rect.topleft = base_rect.midright
            surface.blit(index, index_rect)

        return surface

    def get_text(self, text, size):
        font = pygame.font.Font(pygame.font.get_default_font(), int(options_lib.options["document font size"] * size))
        return font.render(text, True, self.color, self.background_color)

    def get_escape(self, escape, escapes=None):
        if escapes is None:
            escapes = self.escapes

        new_escape = escape[0]

        if new_escape not in escapes:
            raise KeyError(new_escape)

        if len(escape) == 1:
            return escapes[new_escape]

        try:
            return self.get_escape(escape[1:], escapes[new_escape])

        except KeyError as e:
            raise KeyError(new_escape + "." + e.args[0])

    def load_escapes(self):
        import os
        import json

        self.escapes = {}

        files = os.listdir("document_escapes")

        for file_name in files:
            with open("document_escapes/" + file_name) as file:
                self.escapes[file_name.split(".")[0]] = json.load(file)

    def convert_file_to_mathematical(self, file_name, size):
        with open(file_name) as file:
            return self.convert_json_to_mathematical(json.load(file), size)

    def convert_json_to_mathematical(self, json_expression, size, section=None):
        if type(json_expression) is str:
            if len(json_expression) == 0:
                return pygame.Surface((0, 0))

            if json_expression[0] == "/":
                escape = json_expression[1:].split(".")
                return self.convert_json_to_mathematical(self.get_escape(escape), size)

            return self.get_text(json_expression, size)

        if type(json_expression) is list:
            surface = pygame.Surface((0, 0))

            for item_ in json_expression:
                new_surface = self.convert_json_to_mathematical(item_, size)
                surface = self.merge_horizontal(surface, new_surface, size)

            return surface

        if type(json_expression) is dict:
            type_ = json_expression["type"]

            if type_ == "text":
                return self.convert_json_to_mathematical(json_expression["text"],
                                                         size * json_expression["size"])

            if type_ == "vertical":
                surface = pygame.Surface((0, 0))

                for item in json_expression["items"]:
                    new_surface = self.convert_json_to_mathematical(item, size)
                    surface = self.merge_vertical(surface, new_surface, size)

                return surface

            if type_ == "list":
                surface = pygame.Surface((0, 0))

                for item in json_expression["items"]:
                    new_surface = self.convert_json_to_mathematical(item, size)
                    surface = self.list_vertical(surface, new_surface, size)

                return surface

            if type_ == "sections":
                if section is None:
                    section = [0]

                surface = pygame.Surface((0, 0))

                for section_ in json_expression["sections"]:
                    section[-1] += 1

                    new_section = section.copy()
                    new_section.append(0)

                    section_surface = pygame.Surface((0, 0))

                    for item in section_["items"]:
                        new_surface = self.convert_json_to_mathematical(item, size, new_section)
                        section_surface = self.list_vertical(section_surface, new_surface, size)

                    section_name_text = ""

                    for no in section:
                        section_name_text += str(no) + "."

                    title_no_surface = self.get_text(section_name_text, size)
                    title_surface = self.convert_json_to_mathematical(section_["title"], size)
                    title_surface = self.merge_horizontal(title_no_surface, title_surface, size,
                                                          SECTION_TITLE_NO_OFFSET)

                    section_surface = self.list_vertical_with_line(title_surface, section_surface, size, LINE_WIDTH,
                                                                   SECTION_START_OFFSET, INDENT)
                    surface = self.list_vertical(surface, section_surface, size, SECTION_OFFSET)

                return surface

            if type_ == "power":
                left = self.convert_json_to_mathematical(json_expression["base"], size)
                right = self.convert_json_to_mathematical(json_expression["power"], size * 0.75)
                return self.merge_power_index(left, right, None)

            if type_ == "index":
                left = self.convert_json_to_mathematical(json_expression["base"], size)
                right = self.convert_json_to_mathematical(json_expression["index"], size * 0.75)
                return self.merge_power_index(left, None, right)

            if type_ == "power index":
                base = self.convert_json_to_mathematical(json_expression["base"], size)
                index = self.convert_json_to_mathematical(json_expression["index"], size * 0.75)
                power = self.convert_json_to_mathematical(json_expression["power"], size * 0.75)
                return self.merge_power_index(base, power, index)

            if type_ == "ratio":
                numerator = self.convert_json_to_mathematical(json_expression["numerator"], size)
                denominator = self.convert_json_to_mathematical(json_expression["denominator"], size)
                return self.merge_vertical_with_line(numerator, denominator, size, LINE_WIDTH)

            if type_ == "square root":
                inside_surface = self.convert_json_to_mathematical(json_expression["items"], size)

                surface = pygame.Surface(
                    (inside_surface.get_width() + int((2 * DIFF + 3 * ROOT_DELTA + LINE_WIDTH) * size),
                     inside_surface.get_height() + int((LINE_WIDTH + 2 * DIFF) * size)))
                surface.fill((255, 255, 255))
                surface.blit(inside_surface,
                             (int(size * (DIFF + 3 * ROOT_DELTA)), int(size * (LINE_WIDTH_HALF + DIFF))))
                rect = surface.get_rect()

                pygame.draw.lines(surface, self.color, False, ((0, rect.centery),
                                                               (int(size * ROOT_DELTA),
                                                                rect.bottom - int(LINE_WIDTH_HALF * size)),
                                                               (int(size * 3 * ROOT_DELTA),
                                                                int(size * LINE_WIDTH_HALF)),
                                                               (rect.width - int(size * LINE_WIDTH_HALF),
                                                                int(size * LINE_WIDTH_HALF)),
                                                               (rect.width - int(size * LINE_WIDTH_HALF),
                                                                int(size * LINE_WIDTH_HALF + ROOT_LAST_LENGTH))),
                                  int(size * LINE_WIDTH))

                return surface

            if type_ == "root":
                pass

            if type_ == "bracket":
                surface = self.get_text("(", size * 4 / 3)

                for item in json_expression["items"]:
                    surface = self.merge_horizontal(surface, self.convert_json_to_mathematical(item, size), size)

                return self.merge_horizontal(surface, self.get_text(")", size * 4 / 3), size)

            if type_ == "link":
                pass

            raise TypeError(f"Unknown mathematical expression type: {type_}")

        raise TypeError(f"Invalid JSON type, got {type(json_expression)}")


LINE_WIDTH = 3
LINE_WIDTH_HALF = LINE_WIDTH / 2
DIFF = 4
ROOT_LAST_LENGTH = 20
ROOT_DELTA = 5
INDENT = 30
SECTION_START_OFFSET = 10
SECTION_TITLE_NO_OFFSET = 5
SECTION_OFFSET = 25
