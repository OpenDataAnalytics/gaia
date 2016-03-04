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
    r"""
    Filter a GeoPandas DataFrame, return a new filtered DataFrame.
    Currently all filters are joined by 'AND'
    TODO: Support for 'OR', parentheses?
    :param df: The DataFrame to filter
    :param filters: An array of (attribute, operator, value) arrays\
    for example [('city', 'in', ['Boston', 'New York']), ('id', '>', 10)]
    :return: A filtered DataFrame
    """
    for filter in filters:
        attribute = filter[0]
        operator = filter[1]
        values = filter[2]
        if operator.lower() == "in":
            df = df[df[attribute].isin(values)]
        elif operator.lower() == "not in":
            df = df[~df[attribute].isin(values)]
        elif operator.lower() == "contains":
            df = df[df[attribute].str.contains(r'{}'.format(values))]
        elif operator in ops.keys():
            df = df[ops[operator](df[attribute], values)]
    return df


def filter_postgis(filters):
    r"""
    Generate a SQL statement to be used as a WHERE clause.
    TODO: Support parentheses?
    :param filters: list of filters in the form of
    (attribute, operator, values [, join option (AND, OR)])\
    for example [('city', 'in', ['Boston', 'New York']), ('id', '>', 10)]
    :return: SQL string and list of parameters
    """
    sql_filters = None
    sql_params = []
    sql_joiner = ' AND '
    for filter in filters:
        attribute = filter[0]
        operator = filter[1]
        values = filter[2]
        if len(filter) > 3:
            sql_joiner = filter[3]
        if type(values) in (list, tuple):
            sql_filter = '"{}" {} ('.format(attribute, operator) + ','.join(
                ['%s' for x in values]) + ')'
            sql_params.extend(values)
        else:
            sql_filter = '"{}" {} %s'.format(attribute, operator)
            sql_params.append(values)
        if not sql_filters:
            sql_filters = sql_filter
        else:
            sql_filters = sql_filters + sql_joiner + sql_filter
    return sql_filters, sql_params
