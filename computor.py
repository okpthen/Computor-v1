import sys
import re

class Polynom:

    zero_expr = re.compile(r"^(?:([-+]?\d+(?:\.\d+)?)|([-+]?\d*(?:\.\d+)?) ?\*? ?(?:x\^0|1))$")
    one_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?(?:x\^1|x)$")
    two_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?x\^2$")
    any_other_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?x\^(\d{1,2})$")

    valid_charset = "0123456789.*-+=x^"
    PRECISION = 6

    def __init__(self, data):
        self.to_parse = self.check_argv(data)
        self.reduced_values = self.parse_input(self.to_parse)
        self.reduced_form = self.display_reduced_form(self.reduced_values)
        self.values_list = self.extract_values(self.reduced_values)
        self.degree = self.get_degree(self.values_list)

    def __repr__(self):
        rep = "- Polynomial equation info -\n"
        rep += "input: " + self.to_parse
        return rep
    
    #
    # Public
    #

    def check_argv(self, data):
        """check args"""
        if len(data) != 1:
            display_error("args is invalid")
            display_usage()
            exit(0)
        return data[0]
    
    def parse_input(self, to_parse):
        """parse input"""

        print("Received expression:")
        print(to_parse)

        to_parse = to_parse.lower()
        to_parse = re.sub(r"\s", "", to_parse)

        if to_parse.count("=") != 1 or not self.check_characters(to_parse):
            display_error("the provided expression is not a polynomial equation, or contains unexpected characters")
            display_usage()
            exit(0) 

        while re.search(r"(--|\+\+|-\+|\+-)", to_parse):
            to_parse = re.sub(r"(\+\+|--)", "+", to_parse)
            to_parse = re.sub(r"(\+-|-\+)", "-", to_parse)

        to_parse = re.sub(r"([+-])", r" \1", to_parse)
        to_parse = re.sub(r"\s{2,}", " ", to_parse)
        to_parse = re.sub(r"^ -", "-", to_parse)
        to_parse = re.sub(r"= -", "=-", to_parse)

        lhs = to_parse.split("=")[0]
        rhs = to_parse.split("=")[1]

        lhs = lhs.split(" ")
        rhs = rhs.split(" ")
        i = 0
        for member in lhs:
            if member[0] not in "-+":
                lhs[i] = "+" + member
            i += 1

        for member in rhs:
            if member[0] == "-":
                member = "+" + member[1:]
            elif member[0] == "+":
                member = "-" + member[1:]
            else:
                member = "-" + member
            lhs.append(member)

        reduced_values = self.parse_terms(lhs)
        return reduced_values
    
    def parse_terms(self, terms):
        """dict"""

        reduced_degrees = dict()
        problematic_terms = []
        for term in terms:
            degree = 0
            result = re.search(self.zero_expr, term)
            if not result:
                result = re.search(self.one_expr, term)
                degree = 1
            if not result:
                result = re.search(self.two_expr, term)
                degree = 2
            if not result:
                result = re.search(self.any_other_expr, term)
                if result:
                    degree = int(result.group(2))
            if not result:
                problematic_terms.append(term)
            
            if result:
                tmp = 0
                if degree == 0:
                    tmp = result.group(1) if result.group(1) else result.group(2)
                else:
                    tmp = result.group(1)
                if re.search(r"^[+-]$", tmp):
                    tmp += "1"
                tmp = float(tmp)
                if degree in reduced_degrees:
                    reduced_degrees[degree] += tmp
                else:
                    reduced_degrees[degree] = tmp

        if len(problematic_terms) > 0:
            message = "it seems that following term(s) could not be parsed:\n"
            message += '\n'.join(problematic_terms)
            message += "\nPlease check them before retrying"
            display_error(message)
            # display_usage()
            exit(0)

        return reduced_degrees
    
    def display_reduced_form(self, values):
        """
        Displays the reduced equation.
        if the equation has a polynomial degree > 2, the programm will stop here.
        """

        keys = sorted(values.keys())
        reduced = ""
        degree = 0
        for key in keys:
            value = values.get(key)
            value_max_len = len(str(value).split(".")[0]) + self.PRECISION
            if value != 0:
                degree = key
                str_value = format(value, ".%sg" % (value_max_len))
                str_factor = " * x^" + str(key)
                # if key <= 1:
                #     str_factor = "" if key == 0 else " * x"
                if str_value.count(".") == 1 and re.search(r"^0+$", str_value.split(".")[1]):
                    str_value = str_value.split(".")[0]
                if reduced != "":
                    reduced += ("- " if value < 0 else "+ ") + str_value.replace("-", "") + str_factor + " "
                else:
                    reduced += str_value + str_factor + " "
        reduced = re.sub(r"(^1 \* | 1 \* )", " ", reduced)
        reduced = "0" if reduced == "" else reduced
        reduced = reduced.strip() + " = 0"
        print("\nReduced form: " + reduced)
        print("Polynomial degree: " + str(degree))
        if degree > 2:
            display_error("polynomial degree is greater than 2, this script will not attempt to solve this equation.")
            exit(0)
        return reduced

    def extract_values(self, values):
        values_list = [0.0] * 3
        keys = sorted(values.keys())
        for key in keys:
            value = values.get(key)
            if value != 0 and key <= 2:
                values_list[key] = value
        return values_list
    
    def get_degree(self, values):
        degree = 0
        if values[2] != 0:
            degree = 2
        elif values[1] != 0:
            degree = 1
        return degree
    
    def check_characters(self, to_parse):
        for c in to_parse:
            if c not in self.valid_charset:
                return False
        return True
    
    def solve(self):
        """Displays the solution(s) of the equation.
        """

        degree = self.degree
        values = self.values_list
        zero_term = values[0]
        zero_term_max_len = len(str(zero_term).split(".")[0]) + self.PRECISION
        str_zero_term = format(zero_term, ".%sg" % (zero_term_max_len))
        one_term = values[1]
        one_term_max_len = len(str(one_term).split(".")[0]) + self.PRECISION
        str_one_term = format(one_term, ".%sg" % (one_term_max_len))
        two_term = values[2]
        two_term_max_len = len(str(two_term).split(".")[0]) + self.PRECISION
        str_two_term = format(two_term, ".%sg" % (two_term_max_len))
        answer = ""

        if degree == 0:
            if values[0] == 0:
                answer += "\nSolution:\nx = any reel\n"
            else:
                answer += "\nSolution:\nThis is impossible to solve.\n"

        elif degree == 1:

            if zero_term == 0:
                answer += "\nSolution:\nx = 0\n"

            else:
                zero_term = -values[0]
                one_term = values[1]
                result = zero_term / one_term

                answer += "\nSolution:\nx = " + self.get_str_term(result) + "\n"
                
        elif degree == 2:
            if zero_term == 0 and one_term == 0:
                answer += "\nSolution:\nx = 0\n"

            elif zero_term == 0:
                minus_one_term = -one_term
                result = minus_one_term / two_term

                answer += "\nSolutions:\nx1 = 0 and x2 = " + self.get_str_term(result) + "\n"

            else:
                minus_one_term = -one_term
                discriminant = (one_term * one_term) - (4 * two_term * zero_term)


                if discriminant > 0:
                    x1 = (minus_one_term + self.ft_sqrt(discriminant)) / (2 * two_term)
                    x2 = (minus_one_term - self.ft_sqrt(discriminant)) / (2 * two_term)
                    answer += "\nSolutions:\nx1 = " + self.get_str_term(x1) + " and x2 = " + self.get_str_term(x2) + "\n"

                elif discriminant < 0:
                    discriminant = -discriminant
                    real_x = minus_one_term / (2 * two_term)
                    complex_x = self.ft_sqrt(discriminant) / (2 * two_term)
                    
                    answer += "\nSolutions:"
                    str_complex_x = " * " + self.get_str_term(complex_x) if complex_x != 1 else ""
                    answer += "\nx1 = " + self.get_str_term(real_x) + " + i" + str_complex_x + " and x2 = " + self.get_str_term(real_x) + " - i" + str_complex_x + "\n"

                else:
                    x = minus_one_term / (2 * two_term)
                    answer += "\nSolution:"
                    answer += "\nx = " + self.get_str_term(x) + "\n"
        
        print(answer)
        return answer
    
    def get_str_term(self, value):
        str_term_max_len = len(str(value).split(".")[0]) + self.PRECISION
        return format(value, ".%sg" % (str_term_max_len))
    
    def ft_sqrt(self, nb):

        if nb <= 0:
            display_error("this number is not > 0; cannot square root it")
            exit(0)

        guess = nb / 2
        i = 0
        while i < 10:
            bigger = nb / guess if nb / guess >= guess else guess
            smaller = nb / guess if nb / guess < guess else guess
            satisfying_sqrt = 1 if bigger - smaller < 0.0000000001 else 0
            if satisfying_sqrt:
                return guess
            guess = (guess + (nb / guess)) / 2
            i += 1
        return guess


def display_error(message):
    print("\nError: " + message, file=sys.stderr)

def display_usage():
    message = "Usage:\n$> python3 computor.py \"polynomial equation\"\n"
    message += "\nExample of usage:\n$> python3 computor.py \"1 * X^0 + 2 * X^1 = - 1 * X^0 + 4 * X^1\"\n"
    print(message)


def main():
    equation = Polynom(sys.argv[1:])
    answer = equation.solve()

if __name__ == "__main__":
    main()
