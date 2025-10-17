export ARG=$(python3 valid_randexpr_gen.py 1 | tr -d '"')
echo "input = $ARG"
python3 computor.py "$ARG"