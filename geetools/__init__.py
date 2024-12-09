"""The init file of the package."""

__version__ = "0.0.0"
__author__ = "Pierrick Rambaud"
__email__ = "pierrick.rambaud49@gmail.com"


class Hello:
    """Hello world class."""

    msg = "hello world !"
    "the message to print"

    def hello_world(self) -> str:
        """Hello world demo method.

        Returns:
            the hello world string
        """
        return self.msg
