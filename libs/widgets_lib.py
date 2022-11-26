from libs import options_lib
import pygame


class Widget:
    """
    Base widget class. Add super().__init__(shift=shift, alignment=alignment, master_alignment=master_alignment) to
    __init__ when inheriting from this class.
    """

    visible = True
    master = None

    surface: None | pygame.Surface = None
    rect: None | pygame.Rect = None
    full_rect: None | pygame.Rect = None

    alignment: str = "topleft"
    master_alignment: str = "topleft"
    shift: pygame.Vector2 = None

    def __init__(self,
                 shift: pygame.Vector2 = pygame.Vector2(0, 0),
                 alignment: str = "topleft",
                 master_alignment: str = "topleft"):
        self.shift = shift
        self.alignment = alignment
        self.master_alignment = master_alignment

    def set_surface(self, surface):
        self.surface = surface
        self.rect = self.surface.get_rect()
        self.full_rect = self.surface.get_rect()

    def start(self):
        self.update_surface()

    def update_surface(self):
        pass

    def get_top(self):
        if self.master is None:
            return self

        else:
            return self.master

    def ask_for_draw(self, surface: pygame.Surface):
        if not self.visible:
            return

        if self.surface is None:
            self.update_surface()

        surface.blit(self.surface, self.rect)

    def ask_for_event(self, event: pygame.event.Event):
        return False

    def clear_surface(self):
        self.fill_surface((0, 0, 0, 0))

    def fill_surface(self, color: tuple[int, int, int, int] | tuple[int, int, int]):
        self.surface.fill(color)

    def update_rect(self):
        setattr(self.rect, self.alignment, pygame.Vector2(
            getattr(self.master.rect, self.master_alignment)) - self.master.rect.topleft + self.shift)
        self.full_rect = pygame.Rect(pygame.Vector2(self.rect.topleft) + pygame.Vector2(self.master.full_rect.topleft),
                                     self.rect.size)


class ListWidget(Widget):
    """
    Widget class with children. Add
    super().__init__(*args, shift=shift, alignment=alignment, master_alignment=master_alignment) to __init__ when
    inheriting from this class.
    """
    children: list[Widget] = None

    def __init__(self,
                 *args,
                 shift: pygame.Vector2 = pygame.Vector2(0, 0),
                 alignment: str = "topleft",
                 master_alignment: str = "topleft"):
        super().__init__(
            shift,
            alignment,
            master_alignment
        )

        self.children = []
        self.set_children(*args)

    def __iter__(self):
        return iter(self.children)

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

    def ask_for_event(self, event):
        for child in self:
            if child.ask_for_event(event):
                return True

        return False


class Window(ListWidget):
    """
    Window class. Add super().__init__(*args, screen_size=screen_size) to __init__ when inheriting from this class.
    """

    def __init__(self,
                 *args,
                 screen_size):
        super().__init__(
            *args
        )

        self.focused = None
        self.screen_size = screen_size
        self.window_surface = pygame.display.set_mode(tuple(self.screen_size),
                                                      flags=pygame.FULLSCREEN if options_lib.fullscreen else 0)

        self.set_surface(pygame.surface.Surface(self.window_surface.get_size(), pygame.SRCALPHA))

    def event_handler(self, event):
        pass

    def update_surface(self):
        self.clear_surface()

        for child in self:
            child.ask_for_draw(self.surface)

    def render(self):
        self.window_surface.blit(self.surface, (0, 0))

        pygame.display.update()

    def get_events(self):
        events = pygame.event.get()

        for event in events:
            for child in self:
                if child.ask_for_event(event):
                    break

            else:
                self.event_handler(event)


class TextWidget(Widget):
    """
    Text object with one string. Add
    super().__init__(shift=shift, alignment=alignment, master_alignment=master_alignment) to __init__ when
    inheriting from this class.
    """

    def __init__(self,
                 shift: pygame.Vector2,
                 text: bytes | str, font: pygame.font.Font,
                 color: str | tuple,
                 alignment: str = "topleft",
                 master_alignment: str = "topleft",
                 background_color: str | tuple = None):
        super().__init__(
            shift,
            alignment,
            master_alignment)

        self.text = text
        self.font = font
        self.color = color
        self.background = background_color

    def start(self):
        self.update_surface()

    def update_surface(self):
        if not self.visible:
            return

        self.set_surface(self.font.render(self.text, True, self.color, self.background))
        self.update_rect()


class TextListWidget(Widget):
    """
    Text class with more than one strings. Add
    super().__init__(shift=shift, alignment=alignment, master_alignment=master_alignment) to __init__ when
    inheriting from this class.
    """
    surfaces: list[tuple[str, pygame.Surface, pygame.Rect]] = None

    def __init__(self,
                 shift: pygame.Vector2,
                 text: list,
                 font: pygame.font.Font,
                 line_dif: pygame.Vector2,
                 color: str | tuple,
                 background_color: tuple | None = None,
                 alignment="topleft",
                 master_alignment="topleft"):

        super().__init__(
            shift,
            alignment,
            master_alignment)

        self.font = font
        self.color = color
        self.background = background_color

        self.line_dif = line_dif

        self.set_texts(*text)

    def __setitem__(self, key, value):
        surface = self.font.render(value, True, self.color, self.background)
        rect = surface.get_rect()
        setattr(rect, self.alignment, key * self.line_dif)

        self.surfaces[key] = value, surface, rect

    def __getitem__(self, item):
        return self.surfaces[item]

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
        if not self.visible:
            return

        self.set_surface(pygame.Surface(self.get_rect().size, pygame.SRCALPHA))
        self.update_rect()

        for _, surface, rect in self.surfaces:
            self.surface.blit(surface, pygame.Vector2(rect.topleft) - pygame.Vector2(self.get_rect().topleft))


class Button(ListWidget):
    """
    List widget with mouse click detection. Add
    super().__init__(
                *args,
                shift=shift,
                size=size,
                color=color,
                alignment=alignment,
                master_alignment=master_alignment
                button_down_event = button_down_event
                button_up_event = button_up_event
                motion_event = motion_event
        )
    to __init__ when inheriting from this class.
    """

    def __init__(self,
                 *args,
                 shift: pygame.Vector2,
                 size: pygame.Vector2,
                 color: tuple = (0, 0, 0, 0),
                 alignment: str = "topleft",
                 master_alignment: str = "topleft",
                 button_down_event=lambda x: (),
                 button_up_event=lambda x: (),
                 motion_event=lambda x: (),
                 ):
        super(Button, self).__init__(
            *args,
            shift=shift,
            alignment=alignment,
            master_alignment=master_alignment
        )

        self.size = size
        self.color = color

        self.button_down_event = button_down_event
        self.button_up_event = button_up_event
        self.motion_event = motion_event

    def update_surface(self):
        self.set_surface(pygame.Surface(self.size, pygame.SRCALPHA))
        self.update_rect()
        self.fill_surface(self.color)

        for child in self:
            child.ask_for_draw(self.surface)

    def update_rect(self):
        super(Button, self).update_rect()

    @property
    def is_mouse_on(self):
        return self.full_rect.collidepoint(pygame.mouse.get_pos())

    @property
    def local_mouse_position(self):
        return pygame.Vector2(pygame.mouse.get_pos()) - pygame.Vector2(self.full_rect.topleft)

    def ask_for_event(self, event):
        if not (self.visible and self.is_mouse_on):
            return False

        for child in self:
            if child.ask_for_event(event):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.button_down_event(event)
            self.get_top().focused = self

        elif event.type == pygame.MOUSEBUTTONUP:
            self.button_up_event(event)

        elif event.type == pygame.MOUSEMOTION:
            self.motion_event(event)

        return True
