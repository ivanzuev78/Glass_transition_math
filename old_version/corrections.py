class Correction:
    def __init__(self, name, x_max, x_min, inf_pair):
        self.name = name
        self.x_max = x_max
        self.x_min = x_min
        self.inf_pair = inf_pair

    def create_func(self, approx_type, *args):

        if approx_type == "polynomial":

            def polynomial_func(value):
                final = 0
                for power, k in enumerate(args):
                    final += k * value ** power

                return final

            return polynomial_func
