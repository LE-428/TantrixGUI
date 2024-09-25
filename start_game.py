import argparse
import ast
import random
from GUI import solo_tantrix, tantrix_gui
from hexagon_functions import get_neighbor

gui_codes = solo_tantrix.CODES
gui_directions = solo_tantrix.DIRECTIONS


def transform_tantrix_puzzle_to_gui_format(puzzle):
    """Reformat a puzzle of the form:
    [[tiles]],
    [[fields], [tiles]],
    [[fields], [tiles], [rotations]] or
    [[fields], [tiles], [tile_codes], [rotations]]
    """

    def rotate_gui_format(tile, rotation):
        """Generate GUI format of tile by shifting string"""
        new_tile = ''.join([tile[i] for i in [(i + rotation * 5) % 6 for i in [*range(6)]]])
        return new_tile

    def get_path_for_ascending_field_enumeration(puzzle_length):
        """Get a hamiltonian path through the fields (see README for enumeration)"""
        current_field = 0
        search_direction = 1
        visited_fields = 1
        path_edg = []
        while visited_fields < puzzle_length:
            for edge in range(6):
                nbg = get_neighbor(current_field, edge)
                if nbg == current_field + search_direction * 1:
                    path_edg.append(edge)
                    current_field = nbg
                    visited_fields += 1
                    break
                if edge == 5:  # if next field is not in neighborhood of current_field, move down and change search dir.
                    search_direction = -1 * search_direction  # invert the search direction
                    path_edg.append(0)
                    current_field = get_neighbor(current_field, edge=0)
                    visited_fields += 1
        print(path_edg)
        return get_gui_directions_from_path_edges(path_edg)

    path_edges = None
    if len(puzzle) == 1:
        # puzzle.insert(0, [*range(len(puzzle[0]))])  # add fields if only [[tiles]] as input
        out_puzzle = [gui_codes[tile] for tile in puzzle[0]]
        path_edges = get_path_for_ascending_field_enumeration(len(puzzle[0]))
    else:
        if len(puzzle) == 2:
            out_tiles = [gui_codes[tile] for tile in puzzle[1]]
        else:
            out_tiles = [rotate_gui_format(gui_codes[tile],
                                           rotation=puzzle[-1][idx]) for idx, tile in enumerate(puzzle[1])]
        fields = puzzle[0]
        graph = create_graph(fields)
        field_permutation = get_hamiltonian_path(fields, graph)
        # print(f"{field_permutation=}")
        # print(f"{out_tiles=}")
        if field_permutation is not None:
            out_puzzle = [out_tiles[fields.index(perm_tile)] for perm_tile in field_permutation]
            path_edges = get_path_edges(field_permutation)
        else:
            out_puzzle = out_tiles
    return [out_puzzle, path_edges]


def transform_gui_puzzle_to_tantrix_format(tile_value):
    """
    Reformat puzzle from gui format: {(2, 1, 3): 'YBYRRB', (1, 2, 3): 'GBRRGB', (1, 3, 2): 'RBGGRB'}
    into [[fields], [tiles], [rotations]]
    """
#
    def check_tile(tile):
        """Check which tile in solitaire_codes matches the rotated tile and return the rotation"""
        # new_tile = tile
        for idx in range(6):  # rotate tile until it matches
            new_tile = ''.join([tile[i] for i in [(i - idx * 5) % 6 for i in [*range(6)]]])
            if new_tile in gui_codes:
                return gui_codes.index(new_tile), idx  # return the tile number and the rotation
#
    fields = []
    tiles = []
    rotations = []
#
    visited_pieces = 1
    field_index = 0
    search_direction = 1
    current_tile = list(tile_value.keys())[0]
#
    field_and_grid_indices = [(field_index, current_tile)]
    while visited_pieces < len(tile_value.keys()):  # number of tiles placed in gui, every tile must be visited
        # Cycle through the enumeration of the board (see README),
        # find the next index, and check if tile is placed onto field
        for edge in range(6):
            nbr = get_neighbor(field_index, edge)
            # print(f"{edge=}__{nbr=}")
            if nbr == field_index + search_direction * 1:
                # print([nbr])
                gui_dir = get_gui_directions_from_path_edges([edge])
                # print(f"{current_tile=}")
                current_tile = tuple([current_tile[idx] + gui_directions[gui_dir[0]][idx] for idx in range(3)])
                # print(current_tile)
                if current_tile in tile_value.keys():
                    field_and_grid_indices.append((nbr, tuple(current_tile)))
                    visited_pieces += 1
                field_index = nbr
                break
            if edge == 5:
                # print("failing at edge 5")
                # Invert search direction, see enumeration of board in README (index 7 is not a neighbor of index 6)
                search_direction = -1 * search_direction
                field_index = get_neighbor(field_index, edge=0)
                gui_dir = get_gui_directions_from_path_edges(trans_edges=[0])
                current_tile = tuple([current_tile[idx] + gui_directions[gui_dir[0]][idx] for idx in range(3)])
                if current_tile in tile_value.keys():
                    field_and_grid_indices.append((field_index, tuple(current_tile)))
                    visited_pieces += 1
#
    for fidx, grid_idx in field_and_grid_indices:  # generate the output
        grid_code = tile_value[grid_idx]
        tantrix_num, rot = check_tile(grid_code)
        fields.append(fidx)
        tiles.append(tantrix_num)
        rotations.append(rot)
#
    print(f"[{fields}, {tiles}, {rotations}]")
    return [fields, tiles, rotations]


def find_path(graph, start, visited, path):
    """Find a path through the graph defined by the get_neighbor-function between the fields of the solution"""
    visited.add(start)
    path.append(start)
    if len(path) == len(graph):
        return path
    for neighbor in graph[start]:
        if neighbor not in visited:
            result = find_path(graph, neighbor, visited, path)
            if result:
                return result
    visited.remove(start)
    path.pop()
    return None


def get_hamiltonian_path(fields, graph):
    """Find path visiting every field, jumping from neighbor to neighbor"""
    for start in fields:
        visited = set()
        path = []
        result = find_path(graph, start, visited, path)
        if result:
            return result
    return None


def get_gui_directions_from_path_edges(trans_edges):
    """Transform the Tantrix rotation definition into the DIRECTIONS of the GUI"""
    permutation = [1, 0, 5, 4, 3, 2]
    return [permutation[trans_edges[idx]] for idx in range(len(trans_edges))]


def get_path_edges(ham_path):
    """Get the transitioning edges of the tiles on the hamiltonian path"""
    transition_edges = []
    for index, field in enumerate(ham_path[:-1]):
        for edge in range(6):
            if get_neighbor(field, edge) == ham_path[index + 1]:
                transition_edges.append(edge)
                break
    return get_gui_directions_from_path_edges(transition_edges)


def calculate_puzzle_expansion(transition_directions):
    """
    Calculates the maximum and minimum extension of the puzzle along the three axes.
    :param transition_directions: List of directions to transition through.
    :return: List of minimum and maximum extensions along each axis.
    """
    if transition_directions is None:  # if puzzle tiles are not contiguous or form is not allowed
        # (i.e. puzzles with more than one tile that is only connected on one edge to the rest of the puzzle)
        return None
    puzzle_expansion = [[0, 0], [0, 0], [0, 0]]  # [min, max] extension of puzzle in three axes
    cursor = [0, 0, 0]
    for direction in transition_directions:
        # Move the cursor according to the direction
        cursor = [cursor[idx] + gui_directions[direction][idx] for idx in range(3)]
        # Update the puzzle extension for each axis
        for axis in range(3):
            puzzle_expansion[axis][0] = min(cursor[axis], puzzle_expansion[axis][0])
            puzzle_expansion[axis][1] = max(cursor[axis], puzzle_expansion[axis][1])
    return puzzle_expansion


def get_valid_gui_start_point(tiling_size, puzzle_exp):
    """Find all valid points and return the most balanced (central) point."""
    if puzzle_exp is None:  # invalid puzzle
        return None
    min_x, max_x = 0 - puzzle_exp[0][0], tiling_size - puzzle_exp[0][1]
    min_y, max_y = 0 - puzzle_exp[1][0], tiling_size - puzzle_exp[1][1]
    min_z, max_z = 0 - puzzle_exp[2][0], tiling_size - puzzle_exp[2][1]
    valid_points = []
    # Iterate over x and y, and calculate z directly
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            z = tiling_size - (x + y)  # Derive z from x and y
            if min_z <= z <= max_z and z >= 0:
                valid_points.append((x, y, z))
    # If no valid points found, return None
    if not valid_points:
        return None

    # Now find the "most balanced" point (closest to equal distribution of x, y, z)

    def balance_metric(point):
        """Helper function to calculate how balanced a point is."""
        _x, _y, _z = point
        return max(_x, _y, _z) - min(_x, _y, _z)  # Smaller difference means more balanced

    # Sort valid points by balance metric and return the most balanced point
    valid_points.sort(key=balance_metric)
    return valid_points[0]  # Return the most balanced point


def get_board_size(puzzle_size):
    """Get the size (triangle side length) of the GUI game board"""
    pyramid_size = 0  # side length of the pyramid with all puzzle pieces included
    while (pyramid_size + 1) * pyramid_size // 2 < puzzle_size:
        pyramid_size += 1
    board_size = pyramid_size + 2
    return board_size


def create_graph(fields):
    """Create the graph as dictionary with fields as keys and the neighbor fields to every field as entries
    Example: graph = {  0: [1, 2, 3],
                        1: [0, 2],
                        2: [0, 1, 3, 10],
                        3: [0, 2, 10],
                        10: [2, 3] }
            for the fields [0, 1, 2, 3, 10], see field enumeration in README
    """
    graph = {}
    for field in fields:
        # Für jede Zelle alle 6 Nachbarn berechnen
        neighbors = [get_neighbor(field, edge) for edge in range(6)]
        neighbors = [nbg for nbg in neighbors if nbg in fields]
        # In den Graphen eintragen
        graph[field] = neighbors
    return graph


def parse_sol(solution):
    """Try to read input and convert it to solution"""
    output = None
    if isinstance(solution, str):
        try:
            output = ast.literal_eval(solution)
        except (ValueError, SyntaxError):
            print("Invalid format for puzzle argument, using default puzzle instead")
            output = None
    return output


def gen_random_sol(n_tiles=7, kangaroo=1, sample=0, ascending=0, randomness=0, standard=0):
    """
    Function to randomly generate a general solution with a variable number of tiles.

    :param n_tiles: Number of tiles to be used.
    :param kangaroo: If kangaroo=1 (for n_tiles=7), only solutions that can be placed
                     with the kangaroo version are drawn.
    :param sample: If sample=1 and n_tiles > 14, the n_tiles - 14 tiles are randomly drawn from the remaining 42 tiles.
                   sample=1 and n_tiles < 15 corresponds to 14C(n_tiles).
    :param ascending: If ascending=1, the first n_tiles game tiles are taken from the all_tiles array.
    :param randomness: If randomness=1, all tiles are randomly drawn from the 56 tiles.
    :param standard: If standard=1, the solution is returned without the field array.
    :return: Array with randomly generated solution.
    """
    sol_arr = [[] * n_tiles for _ in range(3)]

    def get_tiles(num, kang, asc, rnd, smpl):
        if num == 7:
            if kang:
                return [(i * 2) + random.randint(0, 1) for i in range(7)]
        elif num > 14:
            if smpl:
                return [*range(14)] + random.sample([*range(14, 56)], k=num - 14)
        if smpl:
            return random.sample([*range(0, 14)], k=num)
        if asc:
            return [*range(num)]
        if rnd:
            return random.sample([*range(0, 56)], k=num)
        return random.sample([*range(0, 56)], k=num)

    tiles_vec = get_tiles(num=n_tiles, kang=kangaroo, smpl=sample, asc=ascending, rnd=randomness)
    sol_arr[0] = [*range(n_tiles)]  # The game fields are systematically used in ascending order; for n_tiles=19,
    # two rounds around the center are achieved.
    sol_arr[1] = tiles_vec
    sol_arr[2] = [int(random.uniform(0, 6)) for _ in range(n_tiles)]
    if standard:
        return sol_arr[1:]
    return sol_arr


def main():

    # Puzzle to be used as default or backup
    puzzle = gen_random_sol(kangaroo=0, sample=1, standard=0)
    # Create argument parser
    parser = argparse.ArgumentParser(description="Start a Tantrix Solo game with a given puzzle.")

    # Add argument for puzzle input
    parser.add_argument(
        "-p", "--puzzle",
        type=str,
        default=puzzle,
        help="A list of tile codes representing the puzzle. For example: (see README) \n"
             "\"[[tiles]]\", \n"
             "\"[[fields], [tiles]]\", \n"
             "\"[[fields], [tiles], [rotations]], \n"
             "[[fields], [tiles], [tile_codes], [rotations]]\"",
        required=False
    )

    # Parse arguments
    args = parser.parse_args()

    # Try to read input puzzle
    if parse_sol(args.puzzle) is not None:
        puzzle = parse_sol(args.puzzle)

    # Retrieve the puzzle from input
    # puzzle = args.puzzle

    # Transform user input puzzle to GUI puzzle format
    gui_puzzle, transition_edges = transform_tantrix_puzzle_to_gui_format(puzzle)
    # print(f"{gui_puzzle=} \n {transition_edges=}")

    puzzle_expansion = calculate_puzzle_expansion(transition_edges)
    print(f"{puzzle_expansion=}")

    board_size = get_board_size(len(gui_puzzle))
    print(f"{board_size=}")

    start_hexagon = get_valid_gui_start_point(tiling_size=board_size, puzzle_exp=puzzle_expansion)
    # print(f"{start_hexagon=}")

    # Initialize and start the game with the given puzzle
    tantrix_gui.TantrixGUI(solo_tantrix.Tantrix(gui_puzzle, board_size, start_hexagon, transition_edges),
                           transform_gui_puzzle_to_tantrix_format)


if __name__ == "__main__":
    main()
