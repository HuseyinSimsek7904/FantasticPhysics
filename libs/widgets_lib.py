from libs import options_lib
import pygame


class Widget:
    is_visible = True
    master = None
    surface: None | pygame.Surface = None

    def __init__(self):
        self.surface = pygame.surface.Surface((0, 0), pygame.SRCALPHA)

    def start(self):
        pass

    def update_surface(self):
        pass

    def ask_for_draw(self, surface):
        pass

    def clear_surface(self):
        self.fill_surface((0, 0, 0, 0))

    def fill_surface(self, color: tuple[int, int, int, int] | tuple[int, int, int]):
        self.surface.fill(color)


class LeafWidget(Widget):
    def __init__(self):
        super().__init__()


class ListWidget(Widget):
    children: list[Widget] = None

    def __init__(self, *args):
        super().__init__()

        self.children = []
        self.set_children(*args)

    def __iter__(self):
        return iter(self.children)

    def start(self):
        for child in self:
            child.start()

    def set_children(self, *children: Widget):
        self.kill_children()

        self.add_children(*children)

    def add_child(self, child: Widget):
        if child.master is not None:
            raise ValueError(f"{child} has a master already.")

        child.master = self

        self.children.append(child)

    def add_children(self, *children):
        for child in children:
            self.add_child(child)

    def kill_children(self, *children: Widget):
        for child in children:
            self.kill_child(child)

    def kill_child(self, child: Widget):
        if child.master is not self:
            raise ValueError(f"{child} is not a child.")

        child.master = None

        self.children.remove(child)

    def update_surface(self):
        for child in self:
            child.ask_for_draw(self.surface)


class Window(ListWidget):
    def __init__(self, screen_size, *args):
        super().__init__(*args)

        self.screen_size = screen_size
        self.window_surface = pygame.display.set_mode(tuple(self.screen_size),
                                                      flags=pygame.FULLSCREEN if options_lib.fullscreen else 0)

        self.surface = pygame.surface.Surface(self.window_surface.get_size(), pygame.SRCALPHA)

    def update_surface(self):
        self.clear_surface()

        for child in self:
            child.ask_for_draw(self.surface)

    def render(self):
        self.window_surface.blit(self.surface, (0, 0))

        pygame.display.update()


class TextWidget(LeafWidget):
    def __init__(self, pos: pygame.Vector2, text: bytes | str, font: pygame.font.Font, color: str | tuple,
                 background_color: str | tuple = None):
        super().__init__()

        self.pos = pos
        self.text = text
        self.font = font
        self.color = color
        self.background = background_color

    def start(self):
        self.update_surface()

    def update_surface(self):
        if not self.is_visible:
            return

        self.surface = self.font.render(self.text, True, self.color, self.background)

        super().update_surface()

    def ask_for_draw(self, surface):
        if not self.is_visible:
            return

        surface.blit(self.surface, self.pos)


class TextListWidget(LeafWidget):
    surfaces: list[tuple[str, pygame.Surface, pygame.Rect]] = None

    def __init__(self, pos: pygame.Vector2, text: list, font: pygame.font.Font, color: str | tuple,
                 line_dif: pygame.Vector2, background_color: tuple | None = None, alignment="topleft"):
        super().__init__()

        self.pos = pos
        self.font = font
        self.color = color
        self.background = background_color
        self.alignment = alignment

        self.line_dif = line_dif

        self.set_texts(*text)

    def update_text_at(self, line_no, new_text):
        surface = self.font.render(new_text, True, self.color, self.background)
        rect = surface.get_rect()
        setattr(rect, self.alignment, line_no * self.line_dif)

        self.surfaces[line_no] = new_text, surface, rect

    def set_texts(self, *text):
        self.surfaces = []

        for line_no, line in enumerate(text):
            self.add_text(line)

    def add_text(self, new_text):
        surface = self.font.render(new_text, True, self.color, self.background)
        rect = surface.get_rect()
        setattr(rect, self.alignment, len(self.surfaces) * self.line_dif)

        self.surfaces.append((new_text, surface, rect))

    def get_rect(self):
        left = 0
        right = 0
        top = 0
        bottom = 0

        for _, _, rect in self.surfaces:
            left = min(left, rect.left)
            right = max(right, rect.right)
            top = min(top, rect.top)
            bottom = max(bottom, rect.bottom)

        return pygame.Rect(left, top, right - left, bottom - top)

    def start(self):
        self.update_surface()

    def update_surface(self):
        if not self.is_visible:
            return

        self.surface = pygame.Surface(self.get_rect().size, pygame.SRCALPHA)

        for _, surface, rect in self.surfaces:
            self.surface.blit(surface, pygame.Vector2(rect.topleft) - pygame.Vector2(self.get_rect().topleft))

    def ask_for_draw(self, surface):
        if not self.is_visible:
            return

        rect = self.surface.get_rect()
        setattr(rect, self.alignment, self.pos)
        surface.blit(self.surface, rect)
