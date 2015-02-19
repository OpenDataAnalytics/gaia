cmake_minimum_required(VERSION 3.1)

project(Gaia)

include(CTest)
enable_testing()

find_program(PYTHON_EXECUTABLE python)

option(PYTHON_STATIC_ANALYSIS "Run Python static analysis tests with flake8" ON)
option(PYTHON_COVERAGE "Run tests with coverage.py" ON)
option(PYTHON_BRANCH_COVERAGE "Use branch-level coverage instead of line-level" ON)

if(PYTHON_COVERAGE)
  find_program(PYTHON_COVERAGE_EXECUTABLE coverage)
endif()

if(PYTHON_STATIC_ANALYSIS)
  find_program(FLAKE8_EXECUTABLE flake8)
endif()

if(BUILD_TESTING)
  include(tests/PythonTests.cmake)
  add_subdirectory(tests)
endif()
