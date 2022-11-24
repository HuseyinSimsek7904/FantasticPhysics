from PIL import Image, ImageDraw
import decimal


class TillerSeries:
    # Speed of the particle
    main_coefficient = 1

    # Coefficients of the polynomial
    coefficients = []

    # These are the Tiller options, they change what the series will be
    # Where should the particle start
    pos_start: int | float = 1
    # With how much velocity should the particle start
    vel_start: int | float = 0
    # Bond strength
    W = 1

    # The canvas
    frame: Image.Image = Image.Image()

    # Focus point of the camera (using real coordinates)
    focus_x = 0
    focus_y = 0

    # Zoom of the camera
    x_zoom: int | float = 1
    y_zoom: int | float = 1

    # Used for calculations
    items = None

    def move_to(self, x: float | int, y: float | int) -> None:
        self.focus_x = x
        self.focus_y = y

    def set_size(self, size: tuple[int, int]) -> None:
        self.frame = Image.new("RGB", size)

    def get_real_x(self, x: int | float) -> int | float:
        # Return the real x coordinate of the window x coordinate
        return (x - self.frame.width / 2) * self.x_zoom + self.focus_x

    def get_real_y(self, y) -> int | float:
        # Returns the real y coordinate of the window y coordinate
        return - (y - self.frame.height / 2) * self.y_zoom - self.focus_y

    def get_win_y(self, y) -> int:
        # Returns the window y coordinate of the real y coordinates
        return int((-y - self.focus_y) / self.y_zoom + self.frame.width / 2)

    def generate_frame(self, depth: int) -> None:
        # Render a frame
        self.calculate_coefficients(depth)

        last_y = 0
        last_y1 = 0

        particle_pos = self.pos_start
        particle_vel = self.vel_start

        image = ImageDraw.Draw(self.frame)
        image.line(((0, self.get_win_y(0)), (self.frame.width, self.get_win_y(0))), fill=(255, 0, 0))

        for win_x in range(self.frame.width):
            real_x = self.get_real_x(win_x)

            if real_x < 0:
                continue

            real_y = self.calculate_point(real_x)

            if abs(real_y) > 10:
                # If found number is too big or too small, stop rendering
                return

            win_y = self.get_win_y(real_y)

            # Calculate correct value
            particle_vel += 2 * (1 - particle_pos * self.W) / (particle_pos ** 4) * self.x_zoom
            particle_pos += particle_vel * self.x_zoom
            win_y1 = self.get_win_y(particle_pos)

            # Draw the tiller series
            image.line(((win_x - 1, last_y), (win_x, win_y)))

            # Draw the correct value
            image.line(((win_x - 1, last_y1), (win_x, win_y1)), fill="green")

            last_y = win_y
            last_y1 = win_y1

    def calculate_coefficients(self, depth: int):
        # Calculate the coefficients of the polynomial
        self.coefficients.clear()

        # Every item of coefficients means one item group like 20 * (x^-6) * V
        # (x, V, W, c)
        self.items = [(1, 0, 0, 1)]

        print("Calculating...")
        print(f"Xo = {self.pos_start}")
        print(f"Vo = {self.vel_start}")

        for i in range(depth):
            self.add_coefficient()
            self.print_items(i)

            self.take_derivative_of_items()
            self.simplify_items()

            self.multiply_all_items(1 / (i + 1))

        print("Success!")

        self.print_coefficients()

    def multiply_all_items(self, value):
        for i, (x, v, w, c) in enumerate(self.items):
            self.items[i] = x, v, w, c * value

    def print_items(self, i):
        print(f"{i} -> ", end="")

        for x, v, w, c in self.items:
            print(f"(", end="")

            if c != 1:
                print(c, end="")

            if x == 1:
                print("x", end="")

            elif x != 0:
                print(f"x^{x} ", end="")

            if v == 1:
                print("V", end="")

            elif v != 0:
                print(f"V^{v} ", end="")

            if w == 1:
                print("W", end="")

            elif w != 0:
                print(f"W^{w}", end="")

            print(") + ", end="")

        print("\x08\x08")

    def print_coefficients(self):
        # Prints the calculated coefficients
        for i, coefficient in enumerate(self.coefficients):
            if coefficient == 0:
                continue

            if i == 0:
                print(f"{decimal.Decimal(coefficient)} + ", end="")

            elif i == 1:
                print(f"{decimal.Decimal(coefficient)} * t + ", end="")

            else:
                print(f"{decimal.Decimal(coefficient)} * t^{i} + ", end="")

        print("\x08\x08")

    def simplify_items(self):
        i = 0
        self.items.sort()

        while True:
            if i >= len(self.items) - 1:
                return

            if self.items[i][3] == 0:
                self.items.pop(i)

            elif self.items[i][:3] == self.items[i + 1][:3]:
                self.items[i] = (*self.items[i][:3], self.items[i][3] + self.items[i + 1][3])
                self.items.pop(i + 1)

            else:
                i += 1

    def add_coefficient(self):
        total = 0

        for x, v, w, c in self.items:
            total += c * (self.pos_start ** x) * (self.vel_start ** v) * (self.W ** w)

        self.coefficients.append(total)

    def take_derivative_of_items(self):
        old_items = self.items.copy()
        self.items.clear()

        for item in old_items:
            self.take_derivative(*item)

    def take_derivative(self, x, v, w, c):
        if x != 0:
            self.items.append((x - 1, v + 1, w, c * x))

        if v != 0:
            self.items.append((x - 4, v - 1, w, 2 * c * v))
            self.items.append((x - 3, v - 1, w + 1, -2 * c * v))

    def calculate_point(self, x: int | float) -> int | float:
        # Calculates the position of the particle at any point
        # Just a basic polynomial solver
        # x is time

        result = 0
        out = 1

        for c in self.coefficients:
            result += out * c
            out *= x

        return result

    def save_frame(self, file_name: str) -> None:
        # Save the frame as a file
        self.frame.save(file_name)

    def show(self) -> None:
        # Open the photos program to show the frame
        self.frame.show()

    def focus_left(self, x: int | float) -> None:
        # Move the camera so that the left of the screen is at the given x coordinate (x is real)
        self.focus_x = x + self.frame.width / 2 * self.x_zoom


if __name__ == '__main__':
    # Create a tiller series object and render
    tiller = TillerSeries()
    tiller.set_size((500, 500))
    tiller.x_zoom = 0.005
    tiller.y_zoom = 0.01
    tiller.focus_left(0)

    tiller.pos_start = 1
    tiller.vel_start = 0
    tiller.W = 1

    tiller.generate_frame(1)
    tiller.show()
