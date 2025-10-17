import sys
import re

###
# OBJECT
###

class Polynom:

    #
    # Constants
    #

    zero_expr = re.compile(r"^(?:([-+]?\d+(?:\.\d+)?)|([-+]?\d*(?:\.\d+)?) ?\*? ?(?:x\^0|1))$")
    one_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?(?:x\^1|x)$")
    two_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?x\^2$")
    any_other_expr = re.compile(r"^([-+]?\d*(?:\.\d+)?) ?\*? ?x\^(\d{1,2})$")

    valid_charset = "0123456789.*-+=x^"
    valid_options = "dsuv"
    PRECISION = 6

    option_d = 0
    option_s = 0
    option_u = 0
    option_v = 0

    #
    # Builtins
    #

    def __init__(self, data):
        self.to_parse = self.check_argv(data, len(data))
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

    def check_argv(self, data, nb_args):
        """Options list:
            -d: displays debug about input
            -s: displays reduced form in "scientific" notation (displays all exponents in the form a * x^e)
            -u: ends execution and displays usage
            -v: always displays more info on discriminant step
            -vv: displays every steps with formulas and basic explanations
        """

        if nb_args == 0:
            display_error("no argument provided")
            display_usage()
            exit(0)
        elif nb_args > 1:
            args = ""
            for arg in data[:-1]:
                if arg[0] != "-":
                    display_error("invalid argument - no dash: " + arg)
                    exit(0)
                arg = arg.replace("-", "")
                args += arg
            for letter in args:
                if letter not in self.valid_options:
                    display_error("invalid option: " + letter + ". Please see usage.")
                    display_usage()
                    exit(0)
                elif letter == "d":
                    self.option_d = 1
                elif letter == "s":
                    self.option_s = 1
                elif letter == "u":
                    self.option_u = 1
                    display_usage()
                    exit(0)
                elif letter == "v":
                    self.option_v += 1 if self.option_v < 2 else 0
        return data[nb_args - 1]
        
        


    def parse_input(self, to_parse):
        """This function gets the expression and processes it so it can be resolved.
        There are number of steps, most of them are displayed in console with -d option.
        No arithmetic is done here, only string manipulation.

        return: an array of strings, where each string is a term. If the term is after the '=' in the expression, the sign is reversed.
        """

        print("Received expression:")
        print(to_parse)

        to_parse = to_parse.lower()
        to_parse = re.sub(r"\s", "", to_parse)
        if self.option_d:
            print("\nRemoved spaces:")
            print(to_parse)

        if to_parse.count("=") != 1 or not self.check_characters(to_parse):
            display_error("the provided expression is not a polynomial equation, or contains unexpected characters")
            display_usage()
            exit(0) 

        while re.search(r"(--|\+\+|-\+|\+-)", to_parse):
            to_parse = re.sub(r"(\+\+|--)", "+", to_parse)
            to_parse = re.sub(r"(\+-|-\+)", "-", to_parse)
        if self.option_d:
            print("\nChecked signs:")
            print(to_parse)

        to_parse = re.sub(r"([+-])", r" \1", to_parse)
        to_parse = re.sub(r"\s{2,}", " ", to_parse)
        to_parse = re.sub(r"^ -", "-", to_parse)
        to_parse = re.sub(r"= -", "=-", to_parse)
        if self.option_d:
            print("\nRemade spacing:")
            print(to_parse)

        lhs = to_parse.split("=")[0]
        rhs = to_parse.split("=")[1]
        if self.option_d:
            print("\nLeft part: " + lhs)
            print("Right part: " + rhs)

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
        if self.option_d:
            print("\nTransfer right terms to the left:")
            print(lhs)

        reduced_values = self.parse_terms(lhs)
        return reduced_values


    def parse_terms(self, terms):
        """This function processes values from the array containing all values, then creates a dict

        return: a dictionnary with keys 0, 1, 2, where each key is a polynomial degree.
        NOTE: if a term doesn't match any regular expression used for the parsing, program will stop here and display any suspicious term
        """

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
            exit(0)

        return reduced_degrees


    def display_reduced_form(self, values):
        """Displays the reduced equation.

        When used with the -s option, this will display each exponent instead of using natural form.
        NOTE: if the equation has a polynomial degree > 2, the programm will stop here.
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
                if key <= 1 and not self.option_s:
                    str_factor = "" if key == 0 else " * x"
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

    
    def solve(self):
        """Displays the solution(s) of the equation.

        This function may seem intimidating, but this is mostly text for when -v or -vv options are used.
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
            if self.option_v >= 2:
                answer += "\nDegree is 0. Simple.\n"
            if values[0] == 0:
                answer += "\nSolution:\nx = any reel\n"
            else:
                answer += "\nSolution:\nThis is impossible to solve.\n"

        elif degree == 1:
            if self.option_v >= 2:
                answer += "\nDegree is 1. Not too difficult.\n"

            if zero_term == 0:
                if self.option_v >= 2:
                    answer += "\nHere, the degree 0 term equals 0. There is only one possible value for x in this case.\n"
                answer += "\nSolution:\nx = 0\n"

            else:
                zero_term = -values[0]
                one_term = values[1]
                result = zero_term / one_term

                if self.option_v >= 2:
                    answer += "\n\nFor this case, let's consider this:\n- b is the degree 0 term\n- a is the degree 1 term"
                    answer += "\nTo solve this, we can apply formula: 'x = -b / a'. This translates like this:"
                    answer += "\nx = " + self.get_str_term(zero_term) + " / " + self.get_str_term(one_term) + "\n"
                answer += "\nSolution:\nx = " + self.get_str_term(result) + "\n"
                
        elif degree == 2:
            if self.option_v >= 2:
                answer += "\nDegree is 2. Let's solve that.\nFor the sake of resolution, let's say that:"
                answer += "\n- c is the degree 0 term\n- b is the degree 1 term\n- a is the degree 2 term"

            if zero_term == 0 and one_term == 0:
                if self.option_v >= 2:
                    answer += "\nIn this case we have b = 0 and c = 0. Only the degree 2 term is non-null. There is only one answer in this case.\n"
                answer += "\nSolution:\nx = 0\n"

            elif zero_term == 0:
                minus_one_term = -one_term
                result = minus_one_term / two_term

                if self.option_v >= 2:
                    answer += "\nWe have c = 0. In this case, we can use this formula: x * ( ax + b ) = 0  :  x * ( " + self.get_str_term(two_term) + "x + " + self.get_str_term(one_term) + " ) = 0"
                    answer += "\nThe two solutions in this case are x = 0 and x = -b / a  :  x = " + self.get_str_term(minus_one_term) + " / " + self.get_str_term(two_term) + "\n"
                answer += "\nSolutions:\nx1 = 0 and x2 = " + self.get_str_term(result) + "\n"

            else:
                minus_one_term = -one_term
                discriminant = (one_term * one_term) - (4 * two_term * zero_term)

                if self.option_v >= 2:
                    answer += "\nThe first thing to do is to find the discriminant (Called Delta or Δ). The formula is: Δ = b² - 4ac"
                    answer += "\nΔ = " + self.get_str_term(one_term) + "² - ( 4 * " + self.get_str_term(two_term) + " * " + self.get_str_term(zero_term) + " )"
                if self.option_v >= 1:
                    answer += "\nΔ = " + self.get_str_term(discriminant)

                if discriminant > 0:
                    x1 = (minus_one_term + self.ft_sqrt(discriminant)) / (2 * two_term)
                    x2 = (minus_one_term - self.ft_sqrt(discriminant)) / (2 * two_term)

                    if self.option_v >= 1:
                        answer += "\nDiscriminant is strictly greater than 0. This means there are two real numbers as solutions."
                    if self.option_v >= 2:
                        answer += "\nFormulas for each are: x1 = (-b + √Δ) / 2a  and  x2 = (-b - √Δ) / 2a"
                        answer += "\nSo, x1 = ( " + self.get_str_term(minus_one_term) + " + √" + self.get_str_term(discriminant) + " ) / ( 2 * " + self.get_str_term(two_term) + " )"
                        answer += "\nAnd x2 = ( " + self.get_str_term(minus_one_term) + " - √" + self.get_str_term(discriminant) + " ) / ( 2 * " + self.get_str_term(two_term) + " )\n"
                    answer += "\nSolutions:\nx1 = " + self.get_str_term(x1) + " and x2 = " + self.get_str_term(x2) + "\n"

                elif discriminant < 0:
                    discriminant = -discriminant
                    real_x = minus_one_term / (2 * two_term)
                    complex_x = self.ft_sqrt(discriminant) / (2 * two_term)
                    
                    if self.option_v >= 1:
                        answer += "\nDiscriminant is strictly lower than 0. This means there are two complex numbers as solutions."
                    if self.option_v >= 2:
                        answer += "\nFor this one, we are obligated to introduce a number that allow us to achieve negative square root. But still write Δ as a positive number."
                        answer += "\nFormulas for each solution are: x1 = (-b + i√Δ) / 2a  and  x2 = (-b - i√Δ) / 2a"
                        answer += "\nThis displays like this: x1 = (-b / (2a)) + ((i√Δ) / (2a))  and  x2 = (-b / (2a)) - ((i√Δ) / (2a))"
                        answer += "\nSo, x1 = ((" + self.get_str_term(minus_one_term) + " / ( 2 * " + self.get_str_term(two_term) + " )) + (i√" + self.get_str_term(discriminant) + ") / ( 2 * " + self.get_str_term(two_term) + " ))"
                        answer += "\nAnd x2 = ((" + self.get_str_term(minus_one_term) + " / ( 2 * " + self.get_str_term(two_term) + " )) - (i√" + self.get_str_term(discriminant) + ") / ( 2 * " + self.get_str_term(two_term) + " ))\n"
                    answer += "\nSolutions:"
                    str_complex_x = " * " + self.get_str_term(complex_x) if complex_x != 1 else ""
                    answer += "\nx1 = " + self.get_str_term(real_x) + " + i" + str_complex_x + " and x2 = " + self.get_str_term(real_x) + " - i" + str_complex_x + "\n"

                else:
                    x = minus_one_term / (2 * two_term)
                    if self.option_v >= 1:
                        answer += "\nDiscriminant equals 0. This means the equation has only one real number as solution (more precisely, two identical solutions)"
                    if self.option_v >= 2:
                        answer += "\nIn this case, x can be found with the following formula: x = -b / 2a"
                        answer += "\nHere, x = " + self.get_str_term(minus_one_term) + " / ( 2 * " + self.get_str_term(two_term) + " )\n"
                    answer += "\nSolution:"
                    answer += "\nx = " + self.get_str_term(x) + "\n"
        
        print(answer)
        return answer


    def get_str_term(self, value):
        str_term_max_len = len(str(value).split(".")[0]) + self.PRECISION
        return format(value, ".%sg" % (str_term_max_len))


    def check_characters(self, to_parse):
        for c in to_parse:
            if c not in self.valid_charset:
                return False
        return True

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



###
# OTHER FUNCTIONS
###

def display_usage():
    message = "\nUsage:\n --> python3 <options> computor-v1.py \"polynomial equation\"\n"
    message += "\nNotes:\n"
    message += "- this is a python 3 script, not python 2\n"
    message += "- polynomial degree of reduced form must be 0, 1 or 2\n"
    message += "- no negative or non-integer exponents allowed (valid range: 0 to 99)\n"
    message += "- valid characters set: |" + Polynom.valid_charset +"|\n- x can be written x or X, but every occurence will be lower-cased\n"
    message += "- options must start with a '-' and contain only valid options. See the list below.\n"
    message += "\nOptions list:\n"
    message += "    -d: displays debug about input\n"
    message += "    -s: displays reduced form in \"scientific\" notation (displays all exponents in the form a * x^e)\n"
    message += "    -u: ends execution and displays usage\n"
    message += "    -v: always displays more info on discriminant step\n"
    message += "    -vv: displays every steps with formulas and basic explanations\n"
    message += "\nExample of polynomial equation: 1 * X^0 + 2 * X^1 = - 1 * X^0 + 4 * X^1\n"
    message += "\nExample of usage:\n$> python3 computor-v1.py -s \"1 * X^0 + 2 * X^1 = - 1 * X^0 + 4 * X^1\"\n"
    message += "Reduced form: 2 * x^0 - 2 * x^1 = 0\n"
    message += "Polynomial degree: 1\n"
    message += "Solution:\nx = 1\n"

    print(message)

def display_error(message):
    print("\nError: " + message, file=sys.stderr)


###
# MAIN
###

def main():
    equation = Polynom(sys.argv[1:])
    answer = equation.solve()

# Execute main if this script is directly executed
if __name__ == "__main__":
    main()
