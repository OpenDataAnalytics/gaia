include(CMakeParseArguments)

set(py_coverage_rc "${PROJECT_SOURCE_DIR}/tests/cases/.coveragerc")
set(flake8_config "${PROJECT_SOURCE_DIR}/tests/flake8.cfg")
set(coverage_html_dir "${PROJECT_BINARY_DIR}/www/coverage")
set(_py_testdir "${PROJECT_SOURCE_DIR}/tests/cases")

if(PYTHON_BRANCH_COVERAGE)
  set(_py_branch_cov True)
else()
  set(_py_branch_cov False)
endif()

configure_file(
  "${PROJECT_SOURCE_DIR}/tests/coveragerc.in"
  "${py_coverage_rc}"
  @ONLY
)

if(WIN32)
  set(_separator "\\;")
else()
  set(_separator ":")
endif()

function(python_tests_init)
  if(PYTHON_COVERAGE)
    add_test(
      NAME py_coverage_reset
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" erase
    )
    add_test(
      NAME py_coverage_combine
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" combine
    )
    add_test(
      NAME py_coverage
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" report --fail-under=${COVERAGE_MINIMUM_PASS}
    )
    add_test(
      NAME py_coverage_html
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" html -d "${coverage_html_dir}"
              "--title=Gaia Coverage Report"
    )
    add_test(
      NAME py_coverage_xml
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" xml -o "${PROJECT_BINARY_DIR}/coverage.xml"
    )
    set_property(TEST py_coverage PROPERTY DEPENDS py_coverage_combine)
    set_property(TEST py_coverage_html PROPERTY DEPENDS py_coverage)
    set_property(TEST py_coverage_xml PROPERTY DEPENDS py_coverage)
  endif()
endfunction()

function(add_python_style_test name input)
  if(PYTHON_STATIC_ANALYSIS)
    add_test(
      NAME ${name}
      WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
      COMMAND "${FLAKE8_EXECUTABLE}" "--config=${flake8_config}" "${input}"
    )
  endif()
endfunction()

function(add_python_test case)
  set(name "python_${case}")

  set(_multival_args RESOURCE_LOCKS TIMEOUT)
  cmake_parse_arguments(fn "${_options}" "${_args}" "${_multival_args}" ${ARGN})

  set(module ${case}_test)
  set(pythonpath "")
  set(other_covg "")

  if(PYTHON_COVERAGE)
    add_test(
      NAME ${name}
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_COVERAGE_EXECUTABLE}" run -p --append
              "--source=${PROJECT_SOURCE_DIR}/gaia"
              -m unittest -v ${module}
    )
  else()
    add_test(
      NAME ${name}
      WORKING_DIRECTORY "${_py_testdir}"
      COMMAND "${PYTHON_EXECUTABLE}" -m unittest -v ${module}
    )
  endif()

  set_property(TEST ${name} PROPERTY COST 50)
  if(fn_RESOURCE_LOCKS)
    set_property(TEST ${name} PROPERTY RESOURCE_LOCK ${fn_RESOURCE_LOCKS})
  endif()
  if(fn_TIMEOUT)
    set_property(TEST ${name} PROPERTY TIMEOUT ${fn_TIMEOUT})
  endif()

  if(PYTHON_COVERAGE)
    set_property(TEST ${name} APPEND PROPERTY DEPENDS py_coverage_reset)
    set_property(TEST py_coverage_combine APPEND PROPERTY DEPENDS ${name})
  endif()
endfunction()
