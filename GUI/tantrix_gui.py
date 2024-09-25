import math
import tkinter as tk

# drawing constant
EDGE_LENGTH = 35  # 40, adjust the size of all elements on canvas (and the window)
HEX_HEIGHT = math.sqrt(3.0) * EDGE_LENGTH

COLOR_DICT = {"B": "Blue", "R": "Red", "Y": "Yellow", "G": "Green"}


def dist(pt1, pt2):
    """
    Compute Euclidean distance between two points
    """
    return math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)


def make_hexagon(center):
    """
    Build a hexagon with edges of length EDGE_LENGTH with specified center
    """
    hexagon = [[center[0] + EDGE_LENGTH, center[1]],
               [center[0] + 0.5 * EDGE_LENGTH, center[1] + 0.5 * HEX_HEIGHT],
               [center[0] - 0.5 * EDGE_LENGTH, center[1] + 0.5 * HEX_HEIGHT],
               [center[0] - EDGE_LENGTH, center[1]],
               [center[0] - 0.5 * EDGE_LENGTH, center[1] - 0.5 * HEX_HEIGHT],
               [center[0] + 0.5 * EDGE_LENGTH, center[1] - 0.5 * HEX_HEIGHT],
               [center[0] + EDGE_LENGTH, center[1]]]
    # hexagon = [int(hex_float) for hex_float in hexagon]
    return hexagon


def _create_circle_arc(self, x, y, r, **kwargs):
    """
    Draw a circular arc
    :param self:
    :param x: x-coordinate of center point
    :param y: y-coordinate
    :param r: radius
    :param kwargs: start, end: starting and ending degree
    :return:
    """
    if "start" in kwargs and "end" in kwargs:
        kwargs["extent"] = kwargs.pop("end") - kwargs["start"]
    return self.create_arc(x - r, y - r, x + r, y + r, **kwargs)


tk.Canvas.create_circle_arc = _create_circle_arc  # add function to tkinter class


class TantrixGUI:
    """
    GUI class for game using Tkinter
    """

    def __init__(self, game, button_callback=None):
        """
        Initialize GUI
        """
        self.button_callback = button_callback  # Set the callback function for button press
        self.current_tile_code = None
        self.mouse_position = None
        self.down_click_index = None
        self.grid_centers = None
        self.corners = None
        self._game = game
        self._tiling_size = self._game.get_tiling_size()  # size of board
        self.init_grid()
        self._mouse_drag = False
        self.puzzle_size = self._game.get_puzzle_size()

        self.root = tk.Tk()
        self.root.title("Tantrix Solo")

        # set canvas size
        canvas_width = 2 * EDGE_LENGTH + (3 * self._tiling_size * EDGE_LENGTH // 2)
        canvas_height = (self._tiling_size + 1) * HEX_HEIGHT

        # Create a canvas widget
        self.canvas = tk.Canvas(self.root, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack()
        self.canvas.focus_set()

        # label for number of errors
        self.error_label = tk.Label(self.root, text="Errors: 0")
        self.error_label.pack()

        self.draw()

        # Create buttons
        button_frame = tk.Frame(self.root)  # Create a frame to hold the buttons
        button_frame.pack(pady=10)  # Pack the frame itself

        tk.Button(button_frame, text="Shuffle Tiles", command=self.shuffle_board).pack(side="left", padx=5)
        tk.Button(button_frame, text="Pyramid?", command=self.make_pyramid).pack(side="left", padx=5)

        # Create entry for tiling size and labels
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(pady=10)

        # New puzzle button
        new_puzzle_button = tk.Button(entry_frame, text="New Puzzle", command=self.make_new_puzzle)
        new_puzzle_button.pack(side="left", padx=5)

        # "Tiles:" label
        tiles_label = tk.Label(entry_frame, text="Tiles:")
        tiles_label.pack(side="left", padx=5)

        # Entry field for puzzle size
        self.puzzle_size_entry = tk.Entry(entry_frame, width=10)
        self.puzzle_size_entry.insert(0, str(self._game.get_puzzle_size()))  # Set default value to puzzle_size
        self.puzzle_size_entry.pack(side="left")

        # Boolean variable for checkbox
        self.use_three_colors = tk.BooleanVar()

        # Checkbox for 3 colors
        color_checkbox = tk.Checkbutton(entry_frame, text="3 Colors", variable=self.use_three_colors)
        color_checkbox.pack(side="left", padx=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)  # Use padding to separate from the other elements

        # Button to open the "Instructions" window
        instructions_button = tk.Button(button_frame, text="Game Instructions", command=self.show_instructions)
        instructions_button.pack(side="left", padx=5)  # Use padx for spacing between buttons

        # New Button: Print puzzle
        print_puzzle_button = tk.Button(button_frame, text="Print Puzzle", command=self.print_current_board)
        print_puzzle_button.pack(side="left", padx=5)  # Same horizontal positioning

        # tk.Button(self.root, text="Yellow loop of length 10?", command=self.yellow_loop).pack()
        # tk.Button(self.root, text="Red loop of length 10?", command=self.red_loop).pack()
        # tk.Button(self.root, text="Blue loop of length 10?", command=self.blue_loop).pack()

        keys = {'q': 3, 'w': 4, 'e': 5, 'a': 2, 's': 1, 'd': 0}  # map keys to DIRECTIONS
        for key, direction in keys.items():
            # find keys to method with specific parameter
            self.canvas.bind(f"<KeyPress-{key}>", lambda event, d=direction: self.handle_keypress(d))

        # Bind mouse events
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-3>", self.right_click)

        self.root.mainloop()

    def init_grid(self):
        """
        Precompute triangular grid for use in GUI
        """
        self._tiling_size = self._game.get_tiling_size()  # update the tiling size from game object
        self.corners = [[EDGE_LENGTH, 0.5 * HEX_HEIGHT],
                        [EDGE_LENGTH, (self._tiling_size + 0.5) * HEX_HEIGHT],
                        [EDGE_LENGTH + (3 * self._tiling_size * EDGE_LENGTH // 2),
                         0.5 * (self._tiling_size + 1) * HEX_HEIGHT]]

        self.grid_centers = {}
        for index_i in range(self._tiling_size + 1):
            for index_j in range(self._tiling_size + 1 - index_i):
                grid_index = (index_i, index_j, self._tiling_size - (index_i + index_j))
                grid_center = [0, 0]
                for idx in range(3):
                    grid_center[0] += self.corners[idx][0] * float(grid_index[idx]) // self._tiling_size
                    grid_center[1] += self.corners[idx][1] * float(grid_index[idx]) // self._tiling_size
                self.grid_centers[grid_index] = grid_center

    def closest_grid_center(self, pos):
        """
        Compute index for cell that contains pos
        """
        closest_index = 0
        min_distance = float('inf')
        for grid_index in self.grid_centers.keys():  # loop over all centers
            grid_center = self.grid_centers[grid_index]
            current_distance = dist(pos, grid_center)
            if current_distance < min_distance:
                min_distance = current_distance
                closest_index = grid_index
        return closest_index

    def check_legal(self):
        """
        Button handler to check for legal configuration
        """
        if self._game.is_legal():
            print("Configuration is legal")
        else:
            print("Configuration is illegal")

    def yellow_loop(self):
        """
        Button handler to check for yellow loop
        """
        if not self._game.is_legal():
            print("Configuration is illegal")
        elif self._game.has_loop("Y"):
            print("Configuration has a yellow loop of length 10")
        else:
            print("Configuration does not have a yellow loop of length 10")

    def red_loop(self):
        """
        Button handler to check for red loop
        """
        if not self._game.is_legal():
            print("Configuration is illegal")
        elif self._game.has_loop("R"):
            print("Configuration has a red loop of length 10")
        else:
            print("Configuration does not have a red loop of length 10")

    def blue_loop(self):
        """
        Button handler to check for blue loop
        """
        if not self._game.is_legal():
            print("Configuration is illegal")
        elif self._game.has_loop("B"):
            print("Configuration has a blue loop of length 10")
        else:
            print("Configuration does not have a blue loop of length 10")

    def shuffle_board(self):
        """
        Shuffle all tiles on the board
        """
        self._game.shuffle_tiles()
        self.draw()

    def click(self, event):
        """
        Mouse click handler, integrated with dragging, fires on mouse up
        """
        # print("recognizing click-event")
        self.canvas.focus_set()  # Ensures canvas keeps focus for keypress events
        pos = (event.x, event.y)
        # print(pos)
        up_click_index = self.closest_grid_center(pos)  # find the tile that was meant to be clicked
        # print(up_click_index)  # works fine
        # print(str(self._game))
        # print(self._game.tile_exists(up_click_index))
        if self._mouse_drag and self.current_tile_code:  # replace the tile with the one selected before (drag'n'drop)
            # print("dragging")
            if self._game.tile_exists(up_click_index):  # if tile on mouse release location exists
                # place release location tile on click location tile
                self._game.place_tile(self.down_click_index, self._game.get_code(up_click_index))
                # place the selected tile on the up_click_index either way, if tile is empty, moving the tile
            self._game.place_tile(up_click_index, self.current_tile_code)
        elif self._game.tile_exists(up_click_index) and not self._mouse_drag:  # rotate the selected tile
            # print("rotating...")
            self._game.rotate_tile(up_click_index)
        self._mouse_drag = False
        self.draw()

    def drag(self, event):
        """
        Mouse drag handler, fires on mouse down
        """
        # print("recognizing drag-event")
        self.canvas.focus_set()  # Ensures canvas keeps focus for keypress events
        pos = (event.x, event.y)
        # print(f"dragging-{pos=}")
        if not self._mouse_drag:
            self.down_click_index = self.closest_grid_center(pos)
            # print(self.down_click_index)
            if self._game.tile_exists(self.down_click_index):
                self.current_tile_code = self._game.remove_tile(self.down_click_index)  # pop the tile
            else:
                self.current_tile_code = None  # miss the current grab
            # print(self.current_tile_code)
        self._mouse_drag = True  # indicates a drag operation is happening
        self.mouse_position = pos
        self.draw()

    def right_click(self, event):
        """
        Handles right-click, rotating the selected piece counter-clockwise
        """
        pos = (event.x, event.y)
        # print(pos)
        right_up_click_index = self.closest_grid_center(pos)
        if self._game.tile_exists(right_up_click_index) and not self._mouse_drag:  # rotate the selected tile
            # print("rotating...")
            self._game.rotate_tile_counterclock(right_up_click_index)
        self.draw()

        # print("test")
        # if self.down_click_index and self._game.tile_exists(
        #         self.down_click_index):  # Check, if tile chosen exists
        #     print("rotate")
        #     self._game.rotate_tile(self.down_click_index)  # Rotate tile
        #     self.draw()  # Redraws the board after rotation

    def handle_keypress(self, direction):
        """
        Keys to move around arrangement on the board, key decides the shifting direction
        """
        self._game.try_board_shift(direction)
        self.draw()
        # print(f"Key {direction} was pressed")

    def draw_hexagon(self, center):  # for the empty tiles
        """
        Draw non-fill hexagon on the canvas with given center
        """
        hexagon = make_hexagon(center)
        # Drawing hexagon with lines in Tkinter
        self.canvas.create_polygon([coord for pair in hexagon for coord in pair], outline="black", fill="white")

    def draw_tile(self, center, code):
        """
        Draw a tile based on its center and code using Tkinter's Canvas.
        """
        # Create the hexagon
        hexagon = make_hexagon(center)
        # Draw the hexagon
        self.canvas.create_polygon([coord for pair in hexagon for coord in pair], outline="white", width=2,
                                   fill="black")

        # Midpoints between each pair of adjacent hexagon points
        mid_pts = [[0.5 * (hexagon[idx][dim] + hexagon[idx + 1][dim]) for dim in range(2)]  # hexagon contains vertices
                   for idx in range(len(hexagon) - 1)]

        for color in COLOR_DICT.keys():  # cycle through every color on the tiles
            first = code.find(color)  # find the distance between the two occurrences of the color
            second = code.rfind(color)  # search from the right side
            arc = (second - first) % 6  # arc in [1, 2, 3, 4, 5]

            if arc == 3:  # if 3, the color-matching edges are on the hexagons opposing edges
                # Straight line across the tile
                # (start_points, end_points, thickness, color)
                self.canvas.create_line(mid_pts[first][0], mid_pts[first][1],  # first and second color occurrence
                                        mid_pts[second][0], mid_pts[second][1],
                                        width=EDGE_LENGTH / 4, fill=COLOR_DICT[color])
            elif arc == 2 or arc == 4:  # center point is the center of the neighbor tile between the 2 matching edges
                # Long arc across the tile
                src = second if arc == 4 else first
                src = (src + 2) % 6
                start_ang = 120 + 60 * src
                offset_ang = (start_ang + 180) * math.pi / 180

                cp = [hexagon[src][0] + EDGE_LENGTH * math.cos(offset_ang),  # center point
                      hexagon[src][1] + EDGE_LENGTH * math.sin(offset_ang)]  # starting from vertex of hexagon

                rad = EDGE_LENGTH * 1.5
                pline = []
                for i in range(7):  # 13, 5
                    ang = (start_ang + 10 * i) * math.pi / 180
                    pt = [cp[0] + rad * math.cos(ang), cp[1] + rad * math.sin(ang)]
                    pline.append(pt)

                # Draw the arc as a sequence of lines
                # for i in range(len(pline) - 1):
                #     self.canvas.create_line(pline[i][0], pline[i][1], pline[i + 1][0], pline[i + 1][1],
                #                             width=EDGE_LENGTH / 7, fill=COLOR_DICT[color])

                # Set the starting and ending angle depending on the edge of the hexagon
                if src == 3:
                    start_angle, end_angle = 0, 60
                elif src == 2:
                    start_angle, end_angle = 60, 120
                elif src == 1:
                    start_angle, end_angle = 120, 180
                elif src == 0:
                    start_angle, end_angle = 180, 240
                elif src == 5:
                    start_angle, end_angle = 240, 300
                else:
                    start_angle, end_angle = 300, 360

                start_angle = start_angle + 1  # minor adjustments
                end_angle = end_angle - 1

                # start_angle = (180 - src * 60) % 360
                # end_angle = (start_ang + 60) % 360

                self.canvas.create_circle_arc(x=cp[0], y=cp[1], r=rad, style="arc", outline=COLOR_DICT[color],
                                              width=EDGE_LENGTH / 4, start=start_angle, end=end_angle)
                # self.canvas.create_circle_arc(x=cp[0], y=cp[1], r=rad, style="arc", outline="pink",
                #                               width=EDGE_LENGTH / 7, start=end_angle-5, end=end_angle)

            elif arc == 1 or arc == 5:
                # Short arc between adjacent edges
                # 120 degree arc, centered around shared corner
                src = second if arc == 5 else first
                src = (src + 1) % 6
                cp = hexagon[src]  # center point of the ard
                start_ang = 120 + 60 * src
                rad = EDGE_LENGTH / 2
                pline = []
                for i in range(5):  # 9, 15
                    ang = (start_ang + 30 * i) * math.pi / 180
                    pt = [cp[0] + rad * math.cos(ang), cp[1] + rad * math.sin(ang)]  # polar coordinates
                    pline.append(pt)

                # Draw the arc as a sequence of lines
                # for i in range(len(pline) - 1):
                #     self.canvas.create_line(pline[i][0], pline[i][1], pline[i + 1][0], pline[i + 1][1],
                #                             width=EDGE_LENGTH / 7, fill=COLOR_DICT[color])

                # Set the starting and ending angle depending on the edge of the hexagon
                if src == 2:
                    start_angle, end_angle = 0, 120
                elif src == 1:
                    start_angle, end_angle = 60, 180
                elif src == 0:
                    start_angle, end_angle = 120, 240
                elif src == 5:
                    start_angle, end_angle = 180, 300
                elif src == 4:
                    start_angle, end_angle = 240, 360
                else:
                    start_angle, end_angle = 300, 420

                start_angle = start_angle + 2
                end_angle = end_angle - 2

                self.canvas.create_circle_arc(x=cp[0], y=cp[1], r=rad, style="arc", outline=COLOR_DICT[color],
                                              width=EDGE_LENGTH / 4, start=start_angle, end=end_angle)
                # self.canvas.create_circle_arc(x=cp[0], y=cp[1], r=rad, style="arc", outline="pink",
                #                               width=EDGE_LENGTH / 7, start=end_angle-5, end=end_angle)

    def update_errors(self):
        """
        Update the error counter
        """
        # Call is_legal function from game object
        _, mismatches = self._game.is_legal(count_errors=1)
        # Update label text and color based on mismatches
        if mismatches == 0:
            self.error_label.config(text=f"Errors: {mismatches}", fg="green")
        else:
            self.error_label.config(text=f"Errors: {mismatches}", fg="red")

    def print_current_board(self):
        """
        Function to print the current state of the board to the console
        """
        print("Current board state:")
        # Get the current board state
        board_state = self._game.get_tile_value()
        if self.button_callback:
            self.button_callback(board_state)
        # print(f"{board_state=}")

    def show_instructions(self):
        """
        This function creates a pop-up window that shows game instructions.
        """
        # Create a new window (Toplevel window)
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("Game Instructions")
        # Set the size of the pop-up window
        instructions_window.geometry("300x410")
        # Add a label with instructions text
        instruction_label = tk.Label(instructions_window,
                                     text="How to Play:\n\n1. Match colors on adjacent tiles.\n"
                                          "2. Use left- and right-click to rotate \n the tiles "
                                          "clock-/counterclock-wise.\n"
                                          "3. Left-click tile and drag onto another \n tile or empty field"
                                          " to swap/move tile(s). \n"
                                          "4. Watch the error-counter. \n"
                                          "5. Use \"Shuffle Tiles\" button to \n"
                                          "rearrange all tiles randomly. \n"
                                          "6. Use \"Pyramid?\" button to arrange \n"
                                          "all tiles into pyramid shape. \n"
                                          "7. Use \"New Puzzle\" button to get \n"
                                          "a new puzzle with different tiles \n "
                                          "(change tile number). \n"
                                          "8. Check \"3 Colors\" box to only use \n"
                                          "tiles with 3 different colors \n"
                                          "(when Tiles <= 14). \n"
                                          "9. Use keys 'w'/'s', 'q'/'e' and 'a'/'d' to \n"
                                          "move tile arrangement up/down, \n"
                                          "(top-/bottom-) left/right. \n"
                                          "10. Use \"Print Puzzle\" to print current \n"
                                          "board to console.",
                                     justify="left")
        instruction_label.pack(pady=10)
        # Add a button to close the pop-up window
        close_button = tk.Button(instructions_window, text="Close", command=instructions_window.destroy)
        close_button.pack(pady=10)

    def make_pyramid(self):
        """
        Move all the tiles into the right corner and arrange them into a pyramid
        """
        self._game.move_to_pyramid()
        self.draw()

    def make_new_puzzle(self):
        """
        Read user input for tile size, call game function to create a new puzzle
        """
        try:
            new_puzzle_size = int(self.puzzle_size_entry.get())  # Get value from entry and convert to integer
        except ValueError:
            new_puzzle_size = None
            # print("Invalid tiling size. Please enter a valid number.")
        self._game.new_tiles(num_tiles=new_puzzle_size, three_colors=self.use_three_colors.get())
        self.init_grid()  # recalculate grid after puzzle_size has been changed (update tiling_size in game-file)
        # print(f"{self.grid_centers.keys()=}")
        self.draw()
        self.resize_window()

    def resize_window(self):
        """
        Resize the window after changing the number of tiles (and the size of the board)
        """
        # fit the windows size to the size of the canvas
        self._tiling_size = self._game.get_tiling_size()
        new_canvas_width = 2 * EDGE_LENGTH + (3 * self._tiling_size * EDGE_LENGTH // 2)
        new_canvas_height = (self._tiling_size + 1) * HEX_HEIGHT
        self.canvas.config(width=new_canvas_width, height=new_canvas_height)

    def draw(self):
        """
        Draw everything
        """
        self.canvas.delete("all")  # Clear the canvas before redrawing
        # print(f"{self.grid_centers.keys()=}")
        for grid_index in self.grid_centers.keys():
            grid_center = self.grid_centers[grid_index]  # grid centers where hexagons will be drawn
            if self._game.tile_exists(grid_index):
                self.draw_tile(grid_center, self._game.get_code(grid_index))  # field with tile on it
            else:
                self.draw_hexagon(grid_center)  # empty field (no tile)

        if self._mouse_drag and self.current_tile_code:  # when dnd draw selected tile at cursor position
            self.draw_tile(self.mouse_position, self.current_tile_code)

        self.update_errors()
