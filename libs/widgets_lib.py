import pygame
import typing

pygame.init()

DEBUG_SURFACE_UPDATES = 2 ** 0
DEBUG_POSITION_UPDATES = 2 ** 1
DEBUG_RECT_UPDATES = 2 ** 2
DEBUG_SHOW_RECTS = 2 ** 3

debug_flags = 0


class Widget:
    visible = True
    name = ""
    parent = None

    surface: None | pygame.Surface = None
    expect_update_surface: bool = True

    size: pygame.Vector2 | typing.Iterable[int] = pygame.Vector2()
    expect_update_size: bool = True

    primer_rect: pygame.Rect = None
    expect_update_primer_rect: bool = True

    seconder_rect: pygame.Rect = None
    expect_update_seconder_rect: bool = True

    full_rect: pygame.Rect = None
    expect_update_full_rect: bool = True

    def __init__(
            self,
            name: str = "",
            shift: pygame.Vector2 = pygame.Vector2(0, 0),
            alignment: str = "topleft",
            parent_alignment: str = "topleft"
    ):
        self.name = name
        self.parent: ParentWidget | None = None

        self.shift = shift
        self.alignment = alignment
        self.parent_alignment = parent_alignment

    def show(self):
        self.visible = True

        if not self.is_root:
            self.parent.expect_update_surface = True

    def hide(self):
        self.visible = False

        if not self.is_root:
            self.parent.expect_update_surface = False

    def set_size(self, size):
        self.size = size

        self.expect_update_size = False
        self.expect_update_primer_rect = True
        self.expect_update_seconder_rect = True
        self.expect_update_full_rect = True

        if not self.is_root:
            self.parent.expect_update_surface = True

    def set_shift(self, new_shift: pygame.Vector2):
        self.shift = new_shift

        self.expect_update_seconder_rect = True
        self.expect_update_full_rect = True

        if not self.is_root:
            self.parent.expect_update_surface = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    def get_tree(self, last=True, indent=0):
        return indent * " │ " + f" {'└' if last else '├'}─ <{self.__class__.__name__} {self.name}>"

    @property
    def is_root(self):
        return self.parent is None

    def reset_surface(self):
        self.update_size()
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)

        if debug_flags & DEBUG_SHOW_RECTS:
            pygame.draw.rect(self.surface, (0, 0, 0), ((0, 0), self.surface.get_size()), width=1)

    def update_size(self):
        if not self.expect_update_size:
            return

        # Should be updated when inherited

        self.expect_update_size = False

    def update_surface(self):
        if not self.expect_update_surface:
            return

        # Should be updated when inherited

        self.expect_update_surface = False

        if self.parent is not None:
            self.parent.expect_update_surface = True

    def update_primer_rect(self):
        if not self.expect_update_primer_rect:
            return

        self.primer_rect = pygame.Rect((0, 0), self.size)

        self.expect_update_primer_rect = False

    def update_seconder_rect(self):
        if not self.expect_update_seconder_rect:
            return

        self.update_primer_rect()

        self.seconder_rect = self.primer_rect.copy()

        position = self.parent.get_primer_position(self.parent_alignment) + self.shift
        setattr(self.seconder_rect, self.alignment, position)

        self.expect_update_seconder_rect = False

        self.expect_update_surface = True

        if self.parent is not None:
            self.parent.expect_update_surface = True

    def update_full_rect(self):
        if not self.expect_update_full_rect:
            return

        self.update_seconder_rect()
        self.parent.update_full_rect()

        self.seconder_rect = self.primer_rect.copy()

        position = self.parent.get_full_position(self.parent_alignment) + self.shift
        setattr(self.full_rect, self.alignment, position)

        self.expect_update_full_rect = False

    def get_primer_position(self, alignment: str):
        self.update_primer_rect()
        return getattr(self.primer_rect, alignment)

    def get_seconder_position(self, alignment: str):
        self.update_seconder_rect()
        return getattr(self.seconder_rect, alignment)

    def get_full_position(self, alignment: str):
        self.update_full_rect()
        return getattr(self.full_rect, alignment)

    def find_name(self, name):
        return self if self.name == name else None

    def blit(self, surface: pygame.Surface, rect: pygame.Rect):
        self.surface.blit(surface, rect)

    def ask_for_draw(self):
        if not self.visible:
            return

        self.update_surface()
        self.update_seconder_rect()

        self.parent.blit(self.surface, self.seconder_rect)

    def ask_for_event(self, event: pygame.event.Event):
        return False

    def clear_surface(self):
        self.fill_surface((0, 0, 0, 0))

    def fill_surface(self, color: typing.Iterable[int]):
        self.surface.fill(color)

    def start(self):
        pass

    def get_local_position(self, position: pygame.Vector2):
        return pygame.Vector2(self.full_rect.topleft) + position

    def set_parent(self, parent):
        if self.parent is not None:
            raise ValueError(f"Tried to bind {self} to {parent}, but it was already bound to {self.parent}.")

        if not ParentWidget.__instancecheck__(parent):
            raise ValueError(f"Tried to bind {self} to {parent}, but it was not a ParentWidget.")

        self.parent = parent

    def reset_parent(self):
        if self.parent is None:
            raise ValueError(f"Tried to unbind {self} from its parent, but it does not have one.")

        self.parent = None

    @property
    def delta(self):
        return pygame.Vector2(self.full_rect.topleft) - pygame.Vector2(self.primer_rect.topleft)

    def local_position(self, position: pygame.Vector2):
        return position - pygame.Vector2(self.full_rect.topleft)

    def is_position_on(self, position: pygame.Vector2):
        self.update_full_rect()

        return self.full_rect.collidepoint(pygame.Vector2(position))

    def is_mouse_on(self):
        self.update_full_rect()

        return self.full_rect.collidepoint(self.root_widget.mouse_position)

    @property
    def full_visible(self):
        return self.visible and self.parent.full_visible

    @property
    def root_widget(self):
        return self if self.is_root else self.parent.root_widget

    def get(self, key):
        """
        % finds the child
        $ finds the attribute
        """
        first, other = key.split(".", 1)

        start = first[0]
        name = first[1:]

        match start:
            case "%":
                return self.find_name(name).get(other)

            case "$":
                return getattr(self, name)

            case _:
                return None

    def set(self, key, value):
        """
        % finds the child
        $ finds the attribute
        """
        first, other = key.split(".", 1)

        start = first[0]
        name = first[1:]

        match start:
            case "%":
                self.find_name(name).set(other, value)

            case "$":
                setattr(self, start, value)

            case _:
                return None


class ParentWidget(Widget):
    def __init__(
            self,
            shift: pygame.Vector2,
            name: str = "",
            children: typing.Iterable[Widget] = (),
            alignment: str = "topleft",
            parent_alignment: str = "topleft"
    ):
        Widget.__init__(
            self,
            name=name,
            shift=shift,
            alignment=alignment,
            parent_alignment=parent_alignment
        )

        self.children: list[Widget] = []
        self.set_children(children)

    def find_name(self, name):
        if self.name == name:
            return self

        for child in self:
            found = child.find_name(name)

            if found is not None:
                return found

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, item):
        return self.children[item]

    def __repr__(self):
        match self.children:
            case []:
                return Widget.__repr__(self)

            case [child]:
                return f"<{self.__class__.__name__} {self.__class__} ({child})>"

            case _:
                return f"<{self.__class__.__name__} {self.__class__} ({len(self.children)} children)>"

    def get_tree(self, last=True, indent=0):
        text = Widget.get_tree(self, last, indent)

        for child in self[:-1]:
            text += "\n" + child.get_tree(False, indent + 1)

        text += "\n" + self[-1].get_tree(True, indent + 1)

        return text

    def start(self):
        for child in self:
            child.start()

    def set_children(self, children: typing.Iterable[Widget]):
        self.kill_children(self.children)

        self.add_children(children)

    def add_children(self, children):
        for child in children:
            child.set_parent(self)

            self.children.append(child)

    def kill_children(self, children: typing.Iterable[Widget]):
        for child in children:
            child.reset_parent()

            self.children.remove(child)

    def update_surface(self):
        if not self.expect_update_surface:
            return

        self.reset_surface()
        self.update_primer_rect()

        for child in self:
            child.ask_for_draw()

        self.expect_update_surface = False

        if self.parent is not None:
            self.parent.expect_update_surface = True

    def update_primer_rect(self):
        if not self.expect_update_primer_rect:
            return

        self.update_size()

        self.primer_rect = pygame.Rect((0, 0), self.size)

        self.expect_update_primer_rect = False

        for child in self:
            child.expect_update_seconder_rect = True
            child.expect_update_full_rect = True

    def update_seconder_rect(self):
        if not self.expect_update_seconder_rect:
            return

        self.parent.update_primer_rect()
        self.update_primer_rect()

        self.seconder_rect = self.primer_rect.copy()

        position = self.parent.get_primer_position(self.parent_alignment) + self.shift
        setattr(self.seconder_rect, self.alignment, position)

        self.expect_update_seconder_rect = False

        for child in self:
            child.expect_update_full_rect = True

        if self.parent is not None:
            self.parent.expect_update_surface = True

    def update_full_rect(self):
        if not self.expect_update_full_rect:
            return

        self.update_primer_rect()
        self.update_seconder_rect()

        self.full_rect = self.seconder_rect.copy()

        position = self.parent.get_full_position(self.parent_alignment) + self.shift
        setattr(self.full_rect, self.alignment, position)

        self.expect_update_full_rect = False

        for child in self:
            child.expect_update_full_rect = True

    def ask_for_event(self, event):
        for child in self:
            if child.ask_for_event(event):
                return True

        return False

    def set_size(self, size):
        self.size = size

        self.expect_update_primer_rect = True
        self.expect_update_seconder_rect = True
        self.expect_update_full_rect = True

        for child in self:
            child.expect_update_seconder_rect = True
            child.expect_update_full_rect = True


class FrameWidget(Widget):
    def __init__(
            self,
            shift: pygame.Vector2,
            size: pygame.Vector2,
            name: str = "",
            background_color: typing.Iterable[int] | None = None,
            alignment: str = "topleft",
            parent_alignment: str = "topleft"
    ):
        self.background_color = background_color

        Widget.__init__(
            self,
            name=name,
            shift=shift,
            alignment=alignment,
            parent_alignment=parent_alignment
        )

        self.set_size(size)
        self.expect_update_size = False

    def update_surface(self):
        if not self.expect_update_surface:
            return

        self.reset_surface()

        if self.background_color is not None:
            self.fill_surface(self.background_color)

        self.update_primer_rect()

        self.expect_update_surface = False

        if self.parent is not None:
            self.parent.expect_update_surface = True


class ParentFrameWidget(ParentWidget, FrameWidget):
    def __init__(
            self,
            shift: pygame.Vector2,
            size: pygame.Vector2,
            name: str = "",
            background_color: typing.Iterable[int] = (200, 200, 200),
            children: typing.Iterable[Widget] = (),
            alignment: str = "topleft",
            parent_alignment: str = "topleft"
    ):
        ParentWidget.__init__(
            self,
            name=name,
            shift=shift,
            children=children,
            alignment=alignment,
            parent_alignment=parent_alignment
        )

        self.background_color = background_color
        self.set_size(size)

    def update_surface(self):
        if not self.expect_update_surface:
            return

        self.reset_surface()

        if self.background_color is not None:
            self.fill_surface(self.background_color)

        self.update_primer_rect()

        for child in self:
            child.ask_for_draw()

        self.expect_update_surface = False

        if not self.is_root:
            self.parent.expect_update_surface = True


class Window(ParentFrameWidget):
    window: pygame.Surface = None

    mouse_position: pygame.Vector2 = pygame.Vector2()
    mouse_velocity: pygame.Vector2 = pygame.Vector2()

    def __init__(
            self,
            name: str = "",
            children: typing.Iterable[Widget] = (),
            size: tuple[int, int] | pygame.Vector2 = (0, 0),
            flags: int = 0,
            background_color: typing.Iterable[int] = (0, 0, 0, 0),
    ):
        self.focused = None
        self.flags = flags

        ParentFrameWidget.__init__(
            self,
            name=name,
            shift=pygame.Vector2(),
            size=size,
            children=children,
            background_color=background_color
        )

    def set_size(self, size):
        ParentWidget.set_size(self, size)

        self.window = pygame.display.set_mode(self.size, self.flags)

        self.expect_update_size = False
        self.expect_update_primer_rect = True
        self.expect_update_full_rect = True

        for child in self:
            child.expect_update_seconder_rect = True
            child.expect_update_full_rect = True

    def render(self):
        self.update_surface()
        self.window.blit(self.surface, (0, 0))

        pygame.display.update()

    def event_handler(self, event):
        pass

    def get_events(self):
        self.mouse_position = pygame.Vector2(pygame.mouse.get_pos())
        self.mouse_velocity = pygame.Vector2(pygame.mouse.get_rel())

        events = pygame.event.get()

        for event in events:
            for child in self:
                if child.ask_for_event(event):
                    return

            self.event_handler(event)

    def start(self):
        for child in self:
            child.start()

    def update_seconder_rect(self):
        if not self.expect_update_seconder_rect:
            return

        self.expect_update_seconder_rect = False

    def update_full_rect(self):
        if not self.expect_update_full_rect:
            return

        self.update_primer_rect()

        self.full_rect = self.primer_rect.copy()

        self.expect_update_full_rect = False

    @property
    def full_visible(self):
        return self.visible


class FontStyling:
    font: pygame.font.Font = None

    def __init__(
            self,
            name: str = "Arial",
            size: int = 15,
            bold: bool = False,
            italic: bool = False,
            color: tuple[int, int, int] = (0, 0, 0),
            background_color: tuple[int, int, int] | None = None
    ):
        self.name = name
        self.size = size
        self.bold = bold
        self.italic = italic

        self.color = color
        self.background_color = background_color

        self.update_font()

    def update_font(self):
        self.font = pygame.font.SysFont(self.name, self.size, self.bold, self.italic)

    def render(self, text):
        return self.font.render(text, True, self.color, self.background_color)

    @property
    def height(self):
        return self.font.get_height()


class DynamicTextWidget(FrameWidget):
    items: list[tuple[str, pygame.Surface, pygame.Rect]] = None

    def __init__(
            self,
            shift: pygame.Vector2,
            text: iter,
            name: str = "",
            separation: int = 0,
            font: FontStyling = FontStyling(),

            background_color: typing.Iterable[int] | None = None,

            alignment="topleft",
            parent_alignment="topleft",

            horizontal_padding=0,
            vertical_padding=0,

            text_alignment="left"
    ):

        self.background_color = background_color

        FrameWidget.__init__(
            self,
            name=name,
            shift=shift,
            size=pygame.Vector2(),
            background_color=background_color,
            alignment=alignment,
            parent_alignment=parent_alignment
        )

        self.font = font

        self.horizontal_padding = horizontal_padding
        self.vertical_padding = vertical_padding

        self.separate = separation
        self.text_alignment = text_alignment

        self.items = []

        self.set_texts(text)

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, key: int, value: str | bytes):
        surface = self.font.render(value)
        rect = surface.get_rect()
        rect.top = (self.separate + self.font.height) * key
        setattr(rect, self.text_alignment, 0)

        self.items[key] = value, surface, rect

        self.expect_update_surface = True
        self.expect_update_size = True
        self.expect_update_primer_rect = True
        self.expect_update_seconder_rect = True
        self.expect_update_full_rect = True

        if not self.is_root:
            self.parent.expect_update_surface = True

    def set_texts(self, text):
        self.items.clear()

        for line_no, line in enumerate(text):
            surface = self.font.render(line)
            rect = surface.get_rect()

            rect.top = (self.separate + self.font.height) * line_no
            setattr(rect, self.text_alignment, 0)
            self.items.append((line, surface, rect))

        self.expect_update_surface = True
        self.expect_update_size = True
        self.expect_update_primer_rect = True
        self.expect_update_seconder_rect = True
        self.expect_update_full_rect = True

        if not self.is_root:
            self.parent.expect_update_surface = True

    def update_size(self):
        if not self.expect_update_size:
            return

        left = 0
        right = 0

        for _, _, rect in self.items:
            left = min(left, rect.left)
            right = max(right, rect.right)

        self.size = pygame.Vector2(right - left + self.horizontal_padding * 2,
                                   (self.separate + self.font.height) * len(self.items) + self.vertical_padding * 2)

        self.expect_update_size = False

    def update_surface(self):
        if not self.visible:
            return

        if not self.expect_update_surface:
            return

        self.update_size()

        self.reset_surface()

        if self.background_color is not None:
            self.fill_surface(self.background_color)

        main_rect = pygame.Rect((0, 0), self.size)
        set_x = getattr(main_rect, self.text_alignment)

        for _, surface, rect in self.items:
            new = rect.copy()
            setattr(new, self.text_alignment, set_x)
            self.surface.blit(surface, new)

        self.expect_update_surface = False

        if not self.is_root:
            self.parent.expect_update_surface = True


class ButtonWidget(ParentFrameWidget):
    def __init__(
            self,
            shift: pygame.Vector2,
            size: pygame.Vector2,
            name: str = "",
            children: typing.Iterable[Widget] = (),

            background_color: tuple = (0, 0, 0, 0),

            alignment: str = "topleft",
            parent_alignment: str = "topleft",

            button_down_event=lambda x: (),
            button_up_event=lambda x: (),
            motion_event=lambda x: (),
    ):
        ParentFrameWidget.__init__(
            self,
            name=name,
            size=size,
            children=children,

            shift=shift,
            alignment=alignment,
            parent_alignment=parent_alignment,

            background_color=background_color
        )

        self.button_down_event = button_down_event
        self.button_up_event = button_up_event
        self.motion_event = motion_event

    def ask_for_event(self, event):
        if not (self.full_visible and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN)
                and self.is_mouse_on()):
            return False

        for child in self:
            if child.ask_for_event(event):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.button_down_event(event)
            self.root_widget.focused = self

        elif event.type == pygame.MOUSEBUTTONUP:
            self.button_up_event(event)

        elif event.type == pygame.MOUSEMOTION:
            self.motion_event(event)

        return True


def main():
    def event_handler(event):
        if event.type == pygame.QUIT:
            quit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit()

    window = Window(
        children=(
            FrameWidget(
                name="box",
                shift=pygame.Vector2(50, 50),
                size=pygame.Vector2(100, 100),
                background_color=(100, 100, 100),
                alignment="center",
                parent_alignment="center"
            ),
        ),
        size=(500, 500),
        background_color=(255, 255, 255),
        flags=0
    )
    window.event_handler = event_handler

    box = window.find_name("box")

    while True:
        window.get_events()

        window.render()

        box.set_shift(window.mouse_position)


if __name__ == '__main__':
    main()
