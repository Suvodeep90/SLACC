import sys
import os

sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

import ast
import astor

from analysis.helpers import constants as a_consts
from analysis.helpers import helper
from analysis.parsers import statement_parser
from analysis.blocks import statements as statement_block
from utils import cache
from store import json_store, mongo_store
import properties


DEBUG = False


def get_store(dataset):
  if properties.STORE == "json":
    return json_store.FunctionStore(dataset)
  elif properties.STORE == "mongo":
    return mongo_store.FunctionStore(dataset)
  raise RuntimeError("Invalid configuration: %s" % properties.STORE)


def generate_function_name():
  return "func_%s" % (helper.generate_random_string())


def generate_py_file_name():
  return "%s%s" % (a_consts.GENERATED_PREFIX, helper.generate_random_string())


def print_statements(statement_group):
  for statement in statement_group:
    statement.pprint()


def create_function_nodes(statement_group, function_meta):
  args = ast.arguments(args=[ast.Name(id=variable.name) for variable in function_meta["args"]], vararg=None, kwarg=None,
                       defaults=[])
  function_nodes = {}
  function_body = [statement.get_ast() for statement in statement_group]
  if function_meta["has_return_statement"]:
    name = generate_function_name()
    function_nodes[name] = ast.FunctionDef(name=name, args=args, body=function_body, decorator_list=[])
  else:
    for ret_variable in function_meta["returns"]:
      name = generate_function_name()
      return_statement = ast.Return(value=ast.Name(id=ret_variable.name))
      function_nodes[name] = ast.FunctionDef(name=name, args=args, body=function_body + [return_statement],
                                             decorator_list=[])
  return function_nodes


def get_meta_for_statement_group(statement_group, method, variable_map, local_variables):
  start = statement_group[0].start_pos
  end = statement_group[-1].end_pos
  scope = method.get_scope()
  variables = get_variables_in_range(variable_map[str(scope)], start, end)
  has_return_statement = isinstance(statement_group[-1], statement_block.Statement) and statement_group[-1].is_return
  args = []
  returns = []
  for variable in variables:
    if variable.is_argument(start, local_variables):
      args.append(variable)
    if not has_return_statement and variable.is_updated_in_range(start, end):
      returns.append(variable)
  is_valid = True
  for variable in args:
    if variable.type is None or not variable.type.is_valid:
      is_valid = False
      break
  return {
    "args": args,
    "returns": returns,
    "has_return_statement": has_return_statement,
    "is_valid": is_valid
  }


def create_variable_map(visitor):
  variable_map = {}
  for scope in visitor.scope_variable_map.keys():
    curr_scope = scope
    variables = set()
    while curr_scope:
      for var in visitor.scope_variable_map[curr_scope].values():
        variables.add(var)
      curr_scope = curr_scope.parent
    variable_map[str(scope)] = variables
  return variable_map


def get_variables_in_range(variables, start, end):
  ranged_variables = []
  for variable in variables:
    for pos in variable.positions:
      if start <= pos <= end:
        ranged_variables.append(variable)
        break
  return ranged_variables


def generate_for_file(dataset, file_name):
  store = get_store(dataset)
  visitor = statement_parser.StatementVisitor(file_name, dataset)
  visitor.parse()
  variable_map = create_variable_map(visitor)
  generated_functions = {}
  for method in visitor.methods:
    if DEBUG:
      print("Method Name: %s. Statement Blocks: %d" % (method.name, len(method.statement_blocks)))
    if method.name == a_consts.ROOT_SCOPE: continue
    for statement_group in method.get_statement_groups():
      if DEBUG:
        print("## SG")
        print_statements(statement_group)
        print("\n### Generated")
      # Save type for each function node
      function_meta = get_meta_for_statement_group(statement_group, method, variable_map,
                                                   visitor.scope_variable_map[method.get_scope()].values())
      if not function_meta["is_valid"]:
        if DEBUG:
          print("Not valid")
        continue
      function_nodes = create_function_nodes(statement_group, function_meta)
      arg_types = {}
      for arg in function_meta['args']:
        arg_types[arg['name']] = arg['type'].to_bson()
      for function_name in function_nodes.keys():
        store.update_function_arg_type(function_name, arg_types)
      generated_functions.update(function_nodes)
      if DEBUG:
        print(len(function_nodes))
        # for function_node in function_nodes:
        #   print(astor.to_source(function_node))

  python_file = file_name.split(properties.PYTHON_PROJECTS_HOME)[-1][1:].split(".")[0]
  parent_folder = cache.get_parent_folder(file_name)
  body = ["import sys",
          "sys.path.append('%s')" % properties.PYTHON_PROJECTS_HOME,
          "from %s import *" % python_file.replace(os.path.sep, ".")]
  success, failure = 0, 0
  for function_node in generated_functions.values():
    try:
      function_source = astor.to_source(function_node)
      body.append(function_source)
      success += 1
    except TypeError:
      failure += 1
  if DEBUG:
    print "Success: %d, Failure: %d" % (success, failure)
  content = "\n\n".join(body)
  write_file = os.path.join(parent_folder, "%s.py" % generate_py_file_name())
  cache.write_file(write_file, content)
  return generated_functions




def _test():
  # generate_for_file("codejam", "/Users/panzer/Raise/ProgramRepair/CodeSeer/projects/src/main/python/stupid/dummy.py")
  # generate_for_file("codejam", "/Users/panzer/Raise/ProgramRepair/CodeSeer/projects/src/main/python/Y11R5P1/dennislissov/A.py")
  generate_for_file("codejam", "/Users/panzer/Raise/ProgramRepair/CodeSeer/projects/src/main/python/Y11R5P1/kia/a.py")


if __name__ == "__main__":
  _test()
