import os
import re
import ast


# Utility function to convert CamelCase to snake_case
def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Extracts classes and top-level imports from a module
def extract_classes_and_imports(source):
    tree = ast.parse(source)
    imports = []
    classes = {}
    class_dependencies = {}

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imports.append(node)
        elif isinstance(node, ast.ClassDef):
            class_name = node.name
            class_body = ast.get_source_segment(source, node)
            classes[class_name] = class_body
            class_dependencies[class_name] = extract_dependencies(node)
            print(class_name)

    return imports, classes, class_dependencies


# Extract dependencies of a class
def extract_dependencies(class_node):
    dependencies = set()

    class DependencyVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                dependencies.add(node.id)

    DependencyVisitor().visit(class_node)
    return dependencies


# Convert AST node of import to source code string
def imports_to_source(imports):
    return '\n'.join([ast.unparse(node) for node in imports])


# Create a new module file for each class
def create_class_modules(imports_source, classes, class_dependencies, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    class_files = {class_name: camel_to_snake(class_name) + '.pyi' for class_name in classes}

    classes_modules = []

    for class_name in sorted(classes):
        class_body = classes[class_name]
        module_name = class_files[class_name]
        dependencies = class_dependencies[class_name]
        required_imports = imports_source + '\n'
        for dep in dependencies:
            if dep in class_files and dep != class_name:
                required_imports += f"from .{camel_to_snake(dep)} import {dep}\n"

        file_path = os.path.join(output_dir, module_name)
        with open(file_path, 'w') as f:
            f.write(required_imports + "\n")
            f.write("GenericType1 = typing.TypeVar(\"GenericType1\")\n")
            f.write("GenericType2 = typing.TypeVar(\"GenericType2\")\n\n\n")
            f.write(class_body + "\n")

        classes_modules.append((class_name, module_name.removesuffix(".pyi")))

    # Create '__init__.pyi'.
    with open(os.path.join(output_dir, '__init__.pyi'), 'w') as f:
        f.write("\n__all__ = [\n")
        for class_name, _ in classes_modules:
            f.write(f"    \"{class_name}\",\n")
        f.write("]\n\n")
        for class_name, module_name in classes_modules:
            f.write(f"from .{module_name} import {class_name}\n")


# Main function to split the module
def split_module(input_file, output_dir):
    with open(input_file, 'r') as f:
        source = f.read()

    imports, classes, class_dependencies = extract_classes_and_imports(source)
    imports_source = imports_to_source(imports)
    create_class_modules(imports_source, classes, class_dependencies, output_dir)


if __name__ == '__main__':
    split_module(
        r"C:\Dark Souls\Libraries\Blender Autocomplete 4.1\bpy\types\__init__.pyi",
        r"C:\Dark Souls\Libraries\Blender Autocomplete 4.1\bpy\types\core",
    )
