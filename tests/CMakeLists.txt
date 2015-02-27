set(COVERAGE_MINIMUM_PASS 90)

python_tests_init()

add_python_style_test(python_static_analysis "${PROJECT_SOURCE_DIR}/gaia")
add_python_style_test(python_test_static_analysis "${PROJECT_SOURCE_DIR}/tests")


add_python_test(version)
add_python_test(factory)
add_python_test(gaiaObject)
add_python_test(message)
add_python_test(stream)
add_python_test(port)
