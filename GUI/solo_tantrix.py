"""
Tantrix Solo game

Game is played on a grid of hexagonal tiles
Click on a tile to rotate it.  Click and drag to move a tile.

"""

# run GUI for Tantrix
# import tantrix_gui
import random

# Core modeling idea - a triangular grid of hexagonal tiles are
# modeled by integer tuples of the form (h, k, l)
# where h + k + l == size and h, k, l >= 0.

# Each hexagon has a neighbor in one of six directions
# These directions are modeled by the differences between the 
# tuples of these adjacent tiles

# Numbered directions for hexagonal grid, ordered clockwise at 60 degree intervals, dictionary,
# starting with bottom right edge (hexagon orientated with "flat" side down)
DIRECTIONS = {0: (-1, 0, 1), 1: (-1, 1, 0), 2: (0, 1, -1),
              3: (1, 0, -1), 4: (1, -1, 0), 5: (0, -1, 1)}


def reverse_direction(direction):
    """
    Helper function that returns the opposite direction on a hexagonal grid
    """
    num_directions = len(DIRECTIONS)
    return (direction + num_directions // 2) % num_directions


# Color codes for ten tiles in Tantrix Solitaire
# "B" denotes "Blue", "R" denotes "Red", "Y" denotes "Yellow", "G" denotes "Green"
# Tile coded starting from bottom right edge clockwise
# CODES = ["BBRRYY", "BBRYYR", "BBYRRY", "BRYBYR", "RBYRYB",
#                    "YBRYRB", "BBRYRY", "BBYRYR", "YYBRBR", "YYRBRB"]
CODES = ['BBRYRY', 'BYRBRY', 'RBYYRB', 'BBYRRY', 'RBRYYB', 'YBYRRB', 'BBYRYR',
         'BBRRYY', 'YBRYRB', 'BBRYYR', 'RBYRYB', 'YYBRRB', 'BBYYRR', 'YBRRYB',
         'RYGGRY', 'GYRGRY', 'YYRGRG', 'RRYGGY', 'YYGRGR', 'GYRRGY', 'RYRGGY',
         'YYGGRR', 'YRGYGR', 'YYRGGR', 'RYGRGY', 'YYGRRG', 'YYRRGG', 'GYGRRY',
         'BBRGRG', 'BRGBGR', 'RBGGRB', 'BBGRRG', 'RBRGGB', 'GBGRRB', 'BBGRGR',
         'BBRRGG', 'GBRGRB', 'BBRGGR', 'RBGRGB', 'RRBGGB', 'BBGGRR', 'GBRRGB',
         'BBGYGY', 'BYGBGY', 'GBYYGB', 'BBYGGY', 'GBGYYB', 'YBYGGB', 'BBYGYG',
         'BBGGYY', 'YBGYGB', 'BBGYYG', 'GBYGYB', 'YYBGGB', 'BBYYGG', 'YBGGYB']

# Minimal size of grid to allow placement of 10 tiles
MINIMAL_GRID_SIZE = 4


class Tantrix:
    """
    Basic Tantrix game class
    """

    # def __init__(self, size):
    #     """
    #     Create a triangular grid of hexagons with size + 1 tiles on each side.
    #     """
    #     assert size >= MINIMAL_GRID_SIZE
    #     self._tiling_size = size
    #
    #     # Initialize dictionary tile_value to contain codes for ten
    #     # tiles in Solitaire Tantrix in one 4x4 corner of grid
    #     self._tile_value = {}
    #     _counter = 0
    #     for _h in range(MINIMAL_GRID_SIZE):
    #         for _k in range(MINIMAL_GRID_SIZE - _h):
    #             _l = size - (_h + _k)
    #             grid_index = (_h, _k, _l)
    #             self.place_tile(grid_index, CODES[_counter])
    #             _counter += 1

    def __init__(self, puzzle, tiling_size, start_grid_index=None, transition_edges=None):
        """
        Create a triangular grid of hexagons with size + 1 tiles on each side.
        :param puzzle: list of tile CODES
        :param tiling_size: Size of the pyramid that creates the board (side length)
        :param start_grid_index: Grid index, from which on the board will be initialized
        :param transition_edges: Hexagon edges (see DIRECTIONS),
                                 where the transitions from tile to tile will be happening
        """
        self._tiling_size = None
        self._puzzle_size = len(puzzle)  # number of tiles in puzzle
        if tiling_size is not None:
            self._pyramid_size = tiling_size - 2
            self._tiling_size = tiling_size
        else:
            self.update_pyramid_size()
            self.update_tiling_size()
        self._grid_value = None

        # Initialize dictionary tile_value to contain codes for
        # tiles in grid
        self._tile_value = {}
        init_failed = 1
        break_occurred = False  # Track if a break occurs
        if start_grid_index and transition_edges is not None:  # try to draw exact tile arrangement into board
            curr_grid_index = start_grid_index
            self.place_tile(index=curr_grid_index, code=puzzle[0])
            # print(f"{transition_edges=}")
            for transition_index in range(self._puzzle_size - 1):  # = range(len(transition_edges))
                # print(f"{transition_index=}")
                # curr_grid_index = [curr_grid_index[idx] +
                #                    DIRECTIONS[transition_edges[transition_index]][idx] for idx in range(3)]
                curr_grid_index = self.get_neighbor(curr_grid_index, transition_edges[transition_index])
                if sum(curr_grid_index) > self._tiling_size:  # if next to be placed tile is outside triangular grid
                    break_occurred = True
                    break
                self.place_tile(index=tuple(curr_grid_index), code=puzzle[transition_index + 1])
            if not break_occurred:  # Only set init_failed to 0 if no break occurred
                init_failed = 0

        if init_failed:  # failed, restarting by placing tiles in ascending field order
            self._tile_value = {}  # reset the board in case initialization failed
            _counter = 0
            _index_shift = 0
            _offset = self._puzzle_size - self._pyramid_size * (self._pyramid_size - 1) // 2
            # print(f"{_offset=}")
            if _offset < self._pyramid_size:  # if pyramid is not entirely filled
                _index_shift = 1
            for _h in range(
                    self._pyramid_size - _index_shift):
                for _k in range(self._pyramid_size - _h - _index_shift):  # - 1 workaround
                    _l = self._tiling_size - (_h + _k)
                    grid_index = (_h, _k, _l)
                    self.place_tile(grid_index, puzzle[_counter])
                    _counter += 1
                    if _counter >= self._puzzle_size:
                        return
            if _index_shift:  # Place the remaining tiles that do not complete an entire pyramid side
                _h = 1
                _k = self._pyramid_size - 2
                _l = self._tiling_size - (_h + _k)
                grid_index = (_h, _k, _l)
                # print(f"index_shift-grid_index:{grid_index}")
                self.place_tile(grid_index, puzzle[_counter])
                _counter += 1
                while _counter < self._puzzle_size:
                    # grid_index = [grid_index[idx] +
                    #               DIRECTIONS[4][idx] for idx in range(3)]
                    grid_index = self.get_neighbor(grid_index, direction=4)
                    self.place_tile(tuple(grid_index), puzzle[_counter])
                    _counter += 1

    def __str__(self):
        """
        Return string of dictionary of tile positions and values
        """
        return str(self._tile_value)

    def get_tile_value(self):
        """
        Return dictionary of tile positions and values
        """
        return self._tile_value

    def get_tiling_size(self):
        """
        Return size of board for GUI
        """
        return self._tiling_size

    def get_puzzle_size(self):
        """
        Return size of puzzle (number of tiles)
        """
        return self._puzzle_size

    def get_pyramid_size(self):
        """
        Return size of pyramid (length of pyramid edge)
        """
        return self._pyramid_size

    def update_pyramid_size(self):
        """Update the size of the pyramid fitting every tile from puzzle"""
        pyramid_size = 0
        while (pyramid_size + 1) * pyramid_size // 2 < self._puzzle_size:
            pyramid_size += 1
        self._pyramid_size = pyramid_size

    def update_puzzle_size(self, new_size):
        """Update the puzzle_size with a new value"""
        self._puzzle_size = new_size

    def update_tiling_size(self):
        """Update tiling_size"""
        self._tiling_size = self._pyramid_size + 2

    def tile_exists(self, index):
        """
        Return whether a tile with given index exists
        """
        return index in self._tile_value  # boolean return

    def place_tile(self, index, code):
        """
        Play a tile with code at cell with given index
        """
        self._tile_value[index] = code

    def remove_tile(self, index):
        """
        Remove a tile at cell with given index
        and return the code value for that tile
        """
        return self._tile_value.pop(index)

    def rotate_tile(self, index):
        """
        Rotate a tile clockwise at cell with given index
        """
        _old_string = self._tile_value[index]
        _new_string = _old_string[-1] + _old_string[:-1]  # Shift the code representation of the tile
        self._tile_value[index] = _new_string

    def rotate_tile_counterclock(self, index):
        """
        Rotate a tile counter-clockwise at cell with given index
        """
        _old_string = self._tile_value[index]
        _new_string = _old_string[1:] + _old_string[0]  # Shift the code representation of the tile
        self._tile_value[index] = _new_string

    def shuffle_tiles(self):
        """
        Shuffle the tile_value dictionary by randomly permuting the values across different keys.
        Additionally, rotate each tile between 0 and 5 times after placing it.
        """
        # Copy the current tile_value dictionary
        dict_copy = self._tile_value.copy()
        # Create a list of all tile indices (keys of the dictionary)
        indices = list(self._tile_value.keys())
        # Randomly shuffle the indices
        random.shuffle(indices)
        # Temporary storage for the shuffled tiles
        shuffled_tiles = []
        # Loop through each original index and shuffled index
        for idx, shuffled_idx in zip(dict_copy.keys(), indices):
            # Remove the tile at the current index
            self.remove_tile(idx)
            # Store the shuffled tile and its destination index
            shuffled_tiles.append((idx, dict_copy[shuffled_idx]))
        # Place the shuffled tiles in their new positions
        for idx, tile in shuffled_tiles:
            # Place the tile at its new position
            self.place_tile(idx, tile)
            # Rotate the placed tile between 0 and 5 times randomly
            num_rotations = random.randint(0, 5)
            for _ in range(num_rotations):
                self.rotate_tile(idx)  # Rotate the tile

    def move_to_pyramid(self):
        """
        Move the tiles to the right of the grid and arrange them in a pyramid shape
        """
        codes = list(self._tile_value.values())
        self._tile_value = {}  # Reset the board in case initialization failed
        _counter = 0
        _index_shift = 0
        _offset = self._puzzle_size - self._pyramid_size * (self._pyramid_size - 1) // 2
        # print(f"{_offset=}")
        if _offset < self._pyramid_size:  # If pyramid is not entirely filled
            _index_shift = 1
        for _h in range(self._pyramid_size - _index_shift):
            for _k in range(self._pyramid_size - _h - _index_shift):
                _l = self._tiling_size - (_h + _k)
                grid_index = (_h, _k, _l)
                self.place_tile(grid_index, codes[_counter])
                _counter += 1
                if _counter >= self._puzzle_size:
                    pass
                    # return
        if _index_shift:
            _h = 1
            _k = self._pyramid_size - 2
            _l = self._tiling_size - (_h + _k)
            grid_index = (_h, _k, _l)
            # print(f"index_shift-grid_index:{grid_index}")
            self.place_tile(grid_index, codes[_counter])
            _counter += 1
            while _counter < self._puzzle_size:
                # grid_index = [grid_index[idx] +
                #               DIRECTIONS[4][idx] for idx in range(3)]
                grid_index = self.get_neighbor(grid_index, direction=4)
                self.place_tile(tuple(grid_index), codes[_counter])
                _counter += 1
        # print(f"move_to_pyramid: {self._tile_value=}")

    def new_tiles(self, num_tiles=None, three_colors=None):
        """Create new puzzle by placing new random tiles onto the used and new fields, recieving num_tiles from GUI"""
        old_num = self._puzzle_size
        if num_tiles is None:
            num_tiles = self._puzzle_size
        self.update_puzzle_size(new_size=num_tiles)
        self.update_pyramid_size()
        self.update_tiling_size()
        self.get_grid_coordinates()
        # print(f"{self._grid_value=}")
        if num_tiles != old_num:
            indices = list(self._grid_value)[:num_tiles]  # all fields
        else:
            indices = list(self._tile_value.keys())[:num_tiles]  # all previously filled fields
        if three_colors and num_tiles <= 14:
            color_set = random.randint(0, 3)  # choose random set of 3 colors
            new_codes = random.sample(CODES[color_set * 14:(color_set + 1) * 14], k=num_tiles)
        else:
            new_codes = random.sample(CODES, k=num_tiles)
        self._tile_value = {}  # update the attributes of game object
        for idx, grid_index in enumerate(indices):
            self.place_tile(grid_index, code=new_codes[idx])
        # print(f"{self._tile_value=}")

    def try_board_shift(self, moving_edge):
        """Try to shift all placed tiles into the given direction, do nothing, if board bounds are hurt"""
        # moving_direction = DIRECTIONS[moving_edge]
        shifted_tiles = []
        for grid_index in self._tile_value.keys():
            # shifted_grid_index = [grid_index[idx] + moving_direction[idx] for idx in range(3)]
            shifted_grid_index = self.get_neighbor(grid_index, moving_edge)
            if sum(shifted_grid_index) != self._tiling_size or \
                    any([True for coord in shifted_grid_index if coord < 0]):  # if shift would hurt board borders
                return
            shifted_tiles.append((tuple(shifted_grid_index), self.get_code(grid_index)))
        self._tile_value = {}  # clear the board
        for idx, code in shifted_tiles:  # place the shifted tiles
            self.place_tile(idx, code)

    def get_grid_coordinates(self):
        """
        Update the grid coordinates of the current board after change in tiling_size
        """
        grid_coords = []
        for index_i in range(self._tiling_size + 1):
            for index_j in range(self._tiling_size + 1 - index_i):
                grid_index = (index_i, index_j, self._tiling_size - (index_i + index_j))
                grid_coords.append(grid_index)
        self._grid_value = grid_coords

    def get_code(self, index):
        """
        Return the code of the tile at cell with given index
        """
        return self._tile_value[index]

    def get_neighbor(self, index, direction):
        """
        Return the index of the tile neighboring the tile with given index in given direction
        """
        _neighbor_index = tuple([(index[_dim] + DIRECTIONS[direction][_dim]) for _dim in range(3)])
        return _neighbor_index

    def is_legal(self, count_errors=0):
        """
        Check whether a tile configuration obeys color matching rules for adjacent tiles
        """
        mismatches = 0
        # Check all tiles
        for tile_index in self._tile_value.keys():  # All fields/tiles
            # Check all directions for the selected tile
            for direction in DIRECTIONS.keys():
                neighbor_index = self.get_neighbor(tile_index, direction)
                # Check the color for the selected tile and direction
                if self.tile_exists(neighbor_index):
                    if (self._tile_value[tile_index][direction] !=
                            self.get_code(neighbor_index)[reverse_direction(direction)]):
                        # Different colors so the configuration is illegal
                        if not count_errors:
                            return False
                        else:
                            mismatches += 1
        if not count_errors:
            return True
        else:
            return [mismatches == 0, mismatches // 2]  # mismatches edges are counted two times

    def has_loop(self, color):
        """
        Check whether a tile configuration has a loop of size 10 of given color
        """
        # Check for a legal configuration
        if not self.is_legal():
            return False

        # Choose arbitrary starting point and find your way to the next tile
        tile_indices = list(self._tile_value.keys())  # Convert dict_keys to list
        start_index = tile_indices[0]  # first coordinates e.g. (0, 0, 4), to discover loops
        start_code = self._tile_value[start_index]  # first tile code
        next_direction = start_code.find(color)  # find index of edge with color of interest, gets key of direction
        next_index = self.get_neighbor(start_index, next_direction)
        current_length = 1

        # Loop through neighboring tiles that match given color
        while start_index != next_index:
            current_index = next_index
            # If there is no tile for the right color there is no loop
            if not self.tile_exists(current_index):  # no neighbor in this direction
                return False
            current_code = self._tile_value[current_index]
            # Find the next tile
            if current_code.find(color) == reverse_direction(next_direction):  # get the entering and exiting directions
                next_direction = current_code.rfind(color)  # search from the right side
            else:
                next_direction = current_code.find(color)  # search from the left side
            next_index = self.get_neighbor(current_index, next_direction)
            current_length += 1

        return current_length == len(CODES)

# tantrix_gui.TantrixGUI(Tantrix(4))
# tantrix_gui.TantrixGUI(Tantrix(CODES[:]))
