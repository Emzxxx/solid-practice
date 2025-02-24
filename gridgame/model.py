from collections.abc import Sequence
from abc import ABC, abstractmethod
from .project_types import PlayerId, Cell, Symbol, Feedback, Field

class GameType(ABC):
    @abstractmethod
    def place_symbol(self, symbol: Symbol, cell: Cell,
                    is_game_over: bool, get_symbol_choices: Sequence[Symbol],
                    field: Field) -> Feedback:
        raise NotImplementedError
    
    @abstractmethod
    def winner(self, field: Field, player: PlayerId, symbol: Symbol) -> PlayerId | None:
        raise NotImplementedError
    
    @abstractmethod
    def get_symbol_choices(self, player: PlayerId, player_to_symbol: dict[PlayerId, Symbol]) -> list[Symbol]:
        raise NotImplementedError
    

class TicTacToeGameType(GameType):
    def place_symbol(self, symbol: Symbol, cell: Cell,
                    is_game_over: bool, get_symbol_choices: Sequence[Symbol],
                    field: Field) -> Feedback:
        if is_game_over:
            return Feedback.GAME_OVER

        if symbol not in get_symbol_choices:
            return Feedback.INVALID_SYMBOL

        if not field.is_within_bounds(cell):
            return Feedback.OUT_OF_BOUNDS

        if field.get_symbol_at(cell) is not None:
            return Feedback.OCCUPIED

        field.place_symbol(symbol, cell)

        return Feedback.VALID
    
    def winner(self, field: Field, player: PlayerId, symbol: Symbol) -> PlayerId | None:
        row_groups = [
            [Cell(row, k) for k in field.valid_coords]
            for row in field.valid_coords
        ]

        col_groups = [
            [Cell(k, col) for k in field.valid_coords]
            for col in field.valid_coords
        ]

        diagonals = [
            # Backslash
            [Cell(k, k) for k in field.valid_coords],
            # Forward slash
            [Cell(k, field.grid_size - k + 1)
             for k in field.valid_coords],
        ]

        for groups in [row_groups, col_groups, diagonals]:
            for group in groups:
                if (basis := field.get_symbol_at(group[0])) is not None and \
                        field.are_all_equal_to_basis(basis, group):
                    winner = player
                    assert winner is not None, \
                        f'Winning symbol {basis} in cell group {groups} has no associated player'

                    return winner

        return None
    
    def get_symbol_choices(self, player: PlayerId, player_to_symbol: dict[PlayerId, Symbol]) -> list[Symbol]:
        if player not in player_to_symbol:
            raise ValueError(f'Invalid player: {player}')

        return [player_to_symbol[player]]
    

class WildTicTacToeGameType(GameType):
    def place_symbol(self, symbol: Symbol, cell: Cell,
                    is_game_over: bool, get_symbol_choices: Sequence[Symbol],
                    field: Field) -> Feedback:
        if is_game_over:
            return Feedback.GAME_OVER

        if symbol not in get_symbol_choices:
            return Feedback.INVALID_SYMBOL

        if not field.is_within_bounds(cell):
            return Feedback.OUT_OF_BOUNDS

        if field.get_symbol_at(cell) is not None:
            return Feedback.OCCUPIED

        field.place_symbol(symbol, cell)

        return Feedback.VALID
        
    def winner(self, field: Field, player: PlayerId, symbol: Symbol) -> PlayerId | None:
        row_groups = [
            [Cell(row, k) for k in field.valid_coords]
            for row in field.valid_coords
        ]

        col_groups = [
            [Cell(k, col) for k in field.valid_coords]
            for col in field.valid_coords
        ]

        diagonals = [
            # Backslash
            [Cell(k, k) for k in field.valid_coords],
            # Forward slash
            [Cell(k, field.grid_size - k + 1)
             for k in field.valid_coords],
        ]

        for groups in [row_groups, col_groups, diagonals]:
            for group in groups:
                if (basis := field.get_symbol_at(group[0])) is not None and \
                        field.are_all_equal_to_basis(basis, group):
                    winner = player
                    assert winner is not None, \
                        f'Winning symbol {basis} in cell group {groups} has no associated player'

                    return winner
    
    def get_symbol_choices(self, player: PlayerId, player_to_symbol: dict[PlayerId, Symbol]) -> list[Symbol]:
        if player not in player_to_symbol:
            raise ValueError(f'Invalid player: {player}')
        
        return list(player_to_symbol.values())
        
class NotaktoGameType(GameType):
    def place_symbol(self, symbol: Symbol, cell: Cell,
                    is_game_over: bool, get_symbol_choices: Sequence[Symbol],
                    field: Field) -> Feedback:
        raise NotImplementedError
    
    def winner(self, field: Field, player: PlayerId, symbol: Symbol) -> PlayerId | None:
        raise NotImplementedError
    
    def get_symbol_choices(self, player: PlayerId, player_to_symbol: dict[PlayerId, Symbol]) -> list[Symbol]:
        raise NotImplementedError



class GridGameModel:
    def __init__(self, grid_size: int, player_symbols: Sequence[Symbol], player_count: int,
                game_type: GameType):
        if player_count <= 1:
            raise ValueError(
                f'Must have at least two players (found {player_count})')

        unique_symbols = set(player_symbols)

        if len(unique_symbols) != len(player_symbols):
            raise ValueError(
                f'Player symbols must be unique (was {player_symbols}')

        if len(player_symbols) != player_count:
            raise ValueError(
                f'Player symbols must be exactly {player_count} (was {player_symbols})')


        self._valid_symbols= player_symbols
        self._game_type = game_type

        self._field = Field(grid_size)

        self._player_count = player_count
        self._player_to_symbol: dict[PlayerId, Symbol] = {
            k: symbol
            for k, symbol in enumerate(player_symbols, start=1)
        }
        self._symbol_to_player: dict[Symbol, PlayerId] = {
            symbol: k
            for k, symbol in self._player_to_symbol.items()
        }
        self._current_player: PlayerId = 1

    @property
    def occupied_cells(self) -> dict[Cell, Symbol]:
        return self._field.occupied_cells

    @property
    def grid_size(self):
        return self._field.grid_size

    @property
    def is_game_over(self):
        return (
            self.winner is not None or
            not self._field.has_unoccupied_cell()
        )

    @property
    def current_player(self) -> PlayerId:
        return self._current_player

    @property
    def player_count(self):
        return self._player_count

    @property
    def next_player(self) -> PlayerId:
        return (
            self.current_player + 1 if self.current_player != self.player_count else
            1
        )

    @property
    def winner(self) -> PlayerId | None:
        return self._game_type.winner(self._field, self._current_player, self._player_to_symbol[self._current_player])

    def get_symbol_choices(self, player: PlayerId) -> list[Symbol]:
        return self._game_type.get_symbol_choices(player, self._player_to_symbol)

    def place_symbol(self, symbol: Symbol, cell: Cell) -> Feedback:
        feedback = self._game_type.place_symbol(symbol, cell, self.is_game_over, self._valid_symbols, self._field)
        
        if feedback == Feedback.VALID and not self.is_game_over:
            self._switch_to_next_player()
        
        return feedback

    def _switch_to_next_player(self):
        self._current_player = self.next_player
