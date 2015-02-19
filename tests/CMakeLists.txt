set(COVERAGE_MINIMUM_PASS 90)

python_tests_init()

add_python_style_test(python_static_analysis "${PROJECT_SOURCE_DIR}/gaia")
add_python_style_test(python_test_static_analysis "${PROJECT_SOURCE_DIR}/tests")


# add_python_test(name RESOURCE_LOCKS ...)
