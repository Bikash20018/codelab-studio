"""Explicit, portable source selection and mixed C/C++ project builds."""
import json
import os
from pathlib import Path


SOURCE_SUFFIXES = {'.c', '.cpp', '.cc', '.cxx'}
HEADER_SUFFIXES = {'.h', '.hpp', '.hh', '.hxx'}
IGNORED_DIRS = {'.git', 'build', '.venv', '__pycache__', 'dist', 'node_modules'}
MANIFEST = '.codelab-project.json'


class Project:
    def __init__(self, root, sources=None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError('The project folder does not exist.')
        self.files = self.discover()
        if sources is None and (self.root / MANIFEST).exists():
            try:
                data = json.loads((self.root / MANIFEST).read_text(encoding='utf-8'))
                sources = data['sources']
                if not isinstance(sources, list) or not all(isinstance(s, str) for s in sources):
                    raise ValueError('sources must be a list of file names')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise ValueError(f'Cannot read project settings: {exc}') from exc
        if sources is None:
            sources = [p for p in self.files if p.suffix.lower() in SOURCE_SUFFIXES]
        self.set_sources(sources)

    @classmethod
    def load(cls, root):
        return cls(root)

    def discover(self):
        """Return relative source/header paths, never traversing symbolic links."""
        files = []
        for directory, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = [name for name in dirs if name not in IGNORED_DIRS
                       and not (Path(directory) / name).is_symlink()
                       and not (hasattr(Path(directory) / name, 'is_junction')
                                and (Path(directory) / name).is_junction())]
            for name in names:
                path = Path(directory) / name
                if not path.is_symlink() and path.suffix.lower() in SOURCE_SUFFIXES | HEADER_SUFFIXES:
                    files.append(path.relative_to(self.root))
        return sorted(files, key=lambda p: p.as_posix().lower())

    def set_sources(self, sources):
        selected = []
        for source in sources:
            path = Path(source)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Project sources must stay inside the project folder.')
            full = self.root / path
            if (full.is_symlink() or not full.resolve().is_relative_to(self.root)
                    or any((self.root / Path(*path.parts[:i])).is_symlink()
                           for i in range(1, len(path.parts)))):
                raise ValueError('Symbolic links cannot be selected as project sources.')
            if path.suffix.lower() not in SOURCE_SUFFIXES:
                raise ValueError(f'{path}: select a C or C++ source file, not a header.')
            if not full.is_file():
                raise ValueError(f'Project source is missing: {path}')
            if path not in selected:
                selected.append(path)
        self.sources = selected

    def save(self):
        self.set_sources(self.sources)
        target = self.root / MANIFEST
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps({'version': 1, 'sources': [p.as_posix() for p in self.sources]}, indent=2) + '\n', encoding='utf-8')
        temporary.replace(target)

    def build_steps(self, gcc, gpp, output, extra_flags=()):
        """Compile each selected unit in its language, then link the objects."""
        self.set_sources(self.sources)
        if not self.sources:
            raise ValueError('Select at least one project source file to build.')
        object_dir = self.root / 'build' / 'objects'
        object_dir.mkdir(parents=True, exist_ok=True)
        output = Path(output)
        if not output.is_absolute():
            output = self.root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        steps, objects = [], []
        flags = [str(flag) for flag in extra_flags]
        has_cpp = False
        for index, source in enumerate(self.sources):
            cpp = source.suffix.lower() != '.c'
            has_cpp = has_cpp or cpp
            obj = object_dir / f'{index}_{source.name}.o'
            objects.append(str(obj))
            steps.append([str(gpp if cpp else gcc), *flags, '-x', 'c++' if cpp else 'c',
                          '-std=gnu++17' if cpp else '-std=gnu11', '-g', '-O0', '-Wall',
                          '-I', str(self.root), '-c', str(self.root / source), '-o', str(obj)])
        link = [str(gpp if has_cpp else gcc), *flags, '-g', *objects, '-o', str(output), '-lm']
        if os.name == 'nt':
            link.append('-static')
        steps.append(link)
        return steps
