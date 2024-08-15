class CheckerBoard:
    """
    A class to represent a checkerboard used in calibration or testing.

    Attributes:
        black2BlackCornersHeight_n (int): Number of black-to-black corners in the height direction.
        black2BlackCornersWidth_n (int): Number of black-to-black corners in the width direction.
        placement (str): Description or location of the checkerboard placement.
        squareSideLength_mm (float): Side length of each square on the checkerboard in millimeters.
    """

    def __init__(self, black2BlackCornersHeight_n=4, black2BlackCornersWidth_n=8, placement='backwall', squareSideLength_mm=35):
        """
        Initializes a CheckerBoard instance with the given dimensions and placement.

        Args:
            black2BlackCornersHeight_n (int): Number of black-to-black corners in the height direction. Default is 4.
            black2BlackCornersWidth_n (int): Number of black-to-black corners in the width direction. Default is 8.
            placement (str): Description or location of the checkerboard placement. Default is 'backwall'. Other options are: 'ground', 
            squareSideLength_mm (float): Side length of each square on the checkerboard in millimeters. Default is 35.
        """
        self._black2BlackCornersHeight_n = black2BlackCornersHeight_n
        self._black2BlackCornersWidth_n = black2BlackCornersWidth_n
        self._placement = placement
        self._squareSideLength_mm = squareSideLength_mm

    # Getters and Setters for black2BlackCornersHeight_n
    @property
    def black2BlackCornersHeight_n(self):
        """Get the number of black-to-black corners in the height direction."""
        return self._black2BlackCornersHeight_n

    @black2BlackCornersHeight_n.setter
    def black2BlackCornersHeight_n(self, value: int):
        """Set the number of black-to-black corners in the height direction."""
        if value > 0:
            self._black2BlackCornersHeight_n = value
        else:
            raise ValueError("black2BlackCornersHeight_n must be a positive integer")

    # Getters and Setters for black2BlackCornersWidth_n
    @property
    def black2BlackCornersWidth_n(self):
        """Get the number of black-to-black corners in the width direction."""
        return self._black2BlackCornersWidth_n

    @black2BlackCornersWidth_n.setter
    def black2BlackCornersWidth_n(self, value: int):
        """Set the number of black-to-black corners in the width direction."""
        if value > 0:
            self._black2BlackCornersWidth_n = value
        else:
            raise ValueError("black2BlackCornersWidth_n must be a positive integer")

    # Getters and Setters for placement
    @property
    def placement(self):
        """Get the placement description of the checkerboard."""
        return self._placement

    @placement.setter
    def placement(self, value):
        """Set the placement description of the checkerboard."""
        if isinstance(value, str):
            self._placement = value
        else:
            raise ValueError("placement must be a string")

    # Getters and Setters for squareSideLength_mm
    @property
    def squareSideLength_mm(self):
        """Get the side length of each square on the checkerboard in millimeters."""
        return self._squareSideLength_mm

    @squareSideLength_mm.setter
    def squareSideLength_mm(self, value: int):
        """Set the side length of each square on the checkerboard in millimeters."""
        if value > 0:
            self._squareSideLength_mm = value
        else:
            raise ValueError("squareSideLength_mm must be a positive number")

    def __str__(self):
        """
        Return a string representation of the CheckerBoard instance.

        Returns:
        --------
        str: A string summarizing the key attributes of the checkerboard.
        """
        return (f"CheckerBoard with height: {self.black2BlackCornersHeight_n}, "
                    f"width: {self.black2BlackCornersWidth_n}, "
                    f"each square side length: {self.squareSideLength_mm} mm, "
                    f"placement: {self.placement}.")