from abc import ABC, abstractmethod

class Option(ABC):
    """
    Abstract base class for financial options.
    """

    def __init__(self, spot, strike, maturity, rate, volatility, option_type):

        if spot <= 0:
            raise ValueError("Spot price must be positive.")
        if strike <= 0:
            raise ValueError("Strike price must be positive.")
        if maturity <= 0:
            raise ValueError("Maturity must be positive.")
        if volatility <= 0:
            raise ValueError("Volatility must be non-negative.")
        if option_type.lower() not in ['call', 'put']:
            raise ValueError("option_type must be either 'call' or 'put'.")

        self._spot = spot
        self._strike = strike
        self._maturity = maturity
        self._rate = rate
        self._volatility = volatility
        self._option_type = option_type.lower()

    @property
    def spot(self):
        return self._spot    
        
    @property
    def strike(self):
        return self._strike 
    
    @property
    def maturity(self):
        return self._maturity   
    
    @property
    def rate(self):             
        return self._rate
    
    @property
    def volatility(self):
        return self._volatility
    
    @property
    def option_type(self):
        return self._option_type

    @abstractmethod
    def price(self):
        """
        Abstract method to calculate the price of the option.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def greeks(self):
        """
        Abstract method to calculate the Greeks of the option.
        Must be implemented by subclasses.
        """
        pass