import operator

ops = {
    "=": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def filter_pandas(df, filters):
    """
    Filter a GeoPandas DataFrame, return a new filtered DataFrame
    :param df: The DataFrame to filter
    :param filters: An array of [attribute, operator, value(s) arrays
    :return: A filtered DataFrame
    """
    for filter in filters:
        attribute = filter[0]
        values = filter[1]
        operator = filter[2]
        if operator == "in":
            df = df[df[attribute].isin(values)]
        elif operator == "not in":
            df = df[~df[attribute].isin(values)]
        elif operator in ops.keys():
            df = df[ops[operator](attribute, values)]
    return df
