# Copyright (C) 2016 VIB/BEG/UGent - Tim Diels <timdiels.m@gmail.com>
#
# This file is part of pytil.
#
# pytil is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pytil is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pytil.  If not, see <http://www.gnu.org/licenses/>.

'''
Test pytil.path
'''

from pytil import path as path_
from pytil.test import assert_file_mode
from pathlib import Path
from contextlib import contextmanager
from itertools import product
import plumbum as pb
import tempfile
import hashlib
import pytest
import errno
import os

@pytest.fixture
def path():
    return Path('test')

@pytest.fixture
def contents():
    return 'major contents\nnewlined\n'

@pytest.fixture(autouse=True)
def use_tmp(temp_dir_cwd):
    pass

class TestRemove(object):

    def test_missing(self, path):
        'When remove missing, ignore'
        path_.remove(path)

    def test_file(self, path):
        path.touch()
        path_.remove(path)
        assert not path.exists()

    def test_empty_dir(self, path):
        path.mkdir()
        path_.remove(path)
        assert not path.exists()

    def test_full_dir(self, path):
        path.mkdir()
        (path / 'child').touch()
        (path / 'subdir').mkdir()
        (path / 'subdir' / 'child child').touch()
        path_.remove(path)
        assert not path.exists()

    def test_force(self, path):
        '''
        When force=True, remove file and directories even when read-only
        '''
        path.mkdir()
        child = path / 'file'
        child.touch()
        child.chmod(0o000)
        path.chmod(0o000)
        path_.remove(path, force=True)
        assert not path.exists()

    @pytest.mark.parametrize('symlink_to_file, symlink_in_dir', product(*[(False, True)]*2))
    def test_symlink(self, path, symlink_to_file, symlink_in_dir):
        '''
        When path is symlink, remove symlink, but not its target
        '''
        target_dir = Path('symlink_target')
        target_dir.mkdir()
        target_file = target_dir / 'file'
        target_file.touch()
        if symlink_in_dir:
            path.mkdir()
            source = path / 'source'
        else:
            source = path
        if symlink_to_file:
            source.symlink_to(target_file)
        else:
            source.symlink_to(target_dir)
        path_.remove(path)
        assert not path.exists()
        assert target_dir.exists()
        assert target_file.exists()

class TestChmod(object):

    @pytest.fixture
    def root(self):
        root = Path('root_dir')
        root.mkdir()
        return root

    @pytest.fixture
    def child_dir(self, root):
        child = root / 'child_dir'
        child.mkdir()
        return child

    @pytest.fixture
    def child_file(self, root):
        child = root / 'child_file'
        child.touch()
        return child

    @pytest.fixture
    def grand_child(self, child_dir):
        child = child_dir / 'grand_child'
        child.touch()
        return child

    @contextmanager
    def unchanged(self, *paths):
        paths = {path: path.stat().st_mode for path in paths}
        yield
        paths_new = {path: path.stat().st_mode for path in paths}
        assert paths == paths_new

    @pytest.mark.parametrize('recursive', (False, True))
    def test_file_assign(self, path, recursive):
        path.touch()
        path_.chmod(path, mode=0o777, recursive=recursive)
        assert_file_mode(path, 0o777)
        path_.chmod(path, mode=0o751, recursive=recursive)
        assert_file_mode(path, 0o751)

    @pytest.mark.parametrize('recursive', (False, True))    
    def test_file_add(self, path, recursive):
        path.touch()
        path.chmod(0o000)
        path_.chmod(path, 0o111, '+', recursive=recursive)
        assert_file_mode(path, 0o111)
        path_.chmod(path, 0o100, '+', recursive=recursive)
        assert_file_mode(path, 0o111)
        path_.chmod(path, 0o751, '+', recursive=recursive)
        assert_file_mode(path, 0o751)

    @pytest.mark.parametrize('recursive', (False, True))
    def test_file_subtract(self, path, recursive):
        path.touch()
        path.chmod(0o777)
        path_.chmod(path, 0o111, '-', recursive=recursive)
        assert_file_mode(path, 0o666)
        path_.chmod(path, 0o751, '-', recursive=recursive)
        assert_file_mode(path, 0o026)

    def test_dir_assign(self, root, child_dir, child_file, grand_child):
        with self.unchanged(child_dir, child_file, grand_child):
            path_.chmod(root, mode=0o777)
            assert_file_mode(root, 0o777)
            path_.chmod(root, mode=0o751)
            assert_file_mode(root, 0o751)

    def test_dir_add(self, root, child_dir, child_file, grand_child):
        with self.unchanged(child_dir, child_file, grand_child):
            root.chmod(0o000)
            path_.chmod(root, 0o111, '+')
            assert_file_mode(root, 0o111)
            path_.chmod(root, 0o100, '+')
            assert_file_mode(root, 0o111)
            path_.chmod(root, 0o751, '+')
            assert_file_mode(root, 0o751)

    def test_dir_subtract(self, root, child_dir, child_file, grand_child):
        with self.unchanged(child_dir, child_file, grand_child):
            root.chmod(mode=0o777)
            path_.chmod(root, 0o011, '-')
            assert_file_mode(root, 0o766)
            path_.chmod(root, 0o271, '-')
            assert_file_mode(root, 0o506)

    def test_dir_assign_recursive(self, root, child_dir, child_file, grand_child):
        path_.chmod(root, mode=0o777, recursive=True)
        assert_file_mode(root, 0o777)
        assert_file_mode(child_dir, 0o777)
        assert_file_mode(child_file, 0o666)
        assert_file_mode(grand_child, 0o666)

        path_.chmod(root, mode=0o751, recursive=True)
        assert_file_mode(root, 0o751)
        assert_file_mode(child_dir, 0o751)
        assert_file_mode(child_file, 0o640)
        assert_file_mode(grand_child, 0o640)

    def test_dir_add_recursive(self, root, child_dir, child_file, grand_child):
        grand_child.chmod(0o000)
        child_dir.chmod(0o000)
        child_file.chmod(0o000)
        root.chmod(0o000)

        path_.chmod(root, 0o511, '+', recursive=True)
        assert_file_mode(root, 0o511)
        assert_file_mode(child_dir, 0o511)
        assert_file_mode(child_file, 0o400)
        assert_file_mode(grand_child, 0o400)

        path_.chmod(root, 0o500, '+', recursive=True)
        assert_file_mode(root, 0o511)
        assert_file_mode(child_dir, 0o511)
        assert_file_mode(child_file, 0o400)
        assert_file_mode(grand_child, 0o400)

        path_.chmod(root, 0o751, '+', recursive=True)
        assert_file_mode(root, 0o751)
        assert_file_mode(child_dir, 0o751)
        assert_file_mode(child_file, 0o640)
        assert_file_mode(grand_child, 0o640)

    def test_dir_subtract_recursive(self, root, child_dir, child_file, grand_child):
        root.chmod(mode=0o777)
        child_dir.chmod(0o777)
        child_file.chmod(0o777)
        grand_child.chmod(0o777)

        path_.chmod(root, 0o222, '-', recursive=True)
        assert_file_mode(root, 0o555)
        assert_file_mode(child_dir, 0o555)
        assert_file_mode(child_file, 0o555)
        assert_file_mode(grand_child, 0o555)

        path_.chmod(root, 0o047, '-', recursive=True)
        assert_file_mode(root, 0o510)
        assert_file_mode(child_dir, 0o510)
        assert_file_mode(child_file, 0o511)
        assert_file_mode(grand_child, 0o511)

def test_digest_file(path, contents):
    '''
    When file, digest only its contents
    '''
    path.write_text(contents)
    hash_ = hashlib.sha512()
    hash_.update(contents.encode())
    assert path_.hash(path).hexdigest() == hash_.hexdigest()

class TestDigestDirectory(object):

    @pytest.fixture
    def root(self, contents):
        '''
        Directory tree with its root at 'root'
        '''
        Path('root').mkdir()
        Path('root/subdir1').mkdir()
        Path('root/emptydir').mkdir(mode=0o600)
        Path('root/subdir1/emptydir').mkdir()
        Path('root/file').write_text(contents)
        Path('root/file').chmod(0o600)
        Path('root/emptyfile').touch()
        Path('root/subdir1/subfile').write_text(contents*2)
        return Path('root')

    @pytest.fixture
    def original(self, root):
        return path_.hash(root).hexdigest()

    def test_empty_directory_remove(self, root, original):
        '''
        When empty directory removed, hash changes
        '''
        (root / 'emptydir').rmdir()
        current = path_.hash(root).hexdigest()
        assert original != current

    def test_file_remove(self, root, original):
        '''
        When file removed, hash changes
        '''
        (root / 'file').unlink()
        current = path_.hash(root).hexdigest()
        assert original != current

    def test_file_move(self, root, original):
        '''
        When file moves, hash changes
        '''
        (root / 'file').rename(root / 'subdir1/file')
        current = path_.hash(root).hexdigest()
        assert original != current

    def test_directory_move(self, root, original):
        '''
        When directory moves, hash changes
        '''
        (root / 'emptydir').rename(root / 'subdir1/emptydir')
        current = path_.hash(root).hexdigest()
        assert original != current

    def test_file_content(self, root, original, contents):
        '''
        When file content changes, hash changes
        '''
        (root / 'file').write_text(contents * 3)
        current = path_.hash(root).hexdigest()
        assert original != current

    def test_no_root_name(self, root, original):
        '''
        When root directory renamed, hash unchanged
        '''
        root.rename('notroot')
        current = path_.hash(Path('notroot')).hexdigest()
        assert original == current

    def test_no_root_location(self, root, original):
        '''
        When root directory moved, hash unchanged
        '''
        Path('subdir').mkdir()
        root.rename('subdir/root')
        current = path_.hash(Path('subdir/root')).hexdigest()
        assert original == current

    def test_no_cwd(self, root, original):
        '''
        When current working directory changes, hash unchanged
        '''
        root = root.absolute()
        Path('cwd').mkdir()
        with pb.local.cwd('cwd'):
            current = path_.hash(root).hexdigest()
            assert original == current

    def test_file_dir_stat(self, root, original):
        '''
        When file/dir stat() changes, hash unchanged
        '''
        (root / 'emptydir').chmod(0o404)
        (root / 'file').chmod(0o404)
        current = path_.hash(root).hexdigest()
        assert original == current

class TestTemporaryDirectory:

    @pytest.fixture
    def cleanup(self, mocker):
        return mocker.patch.object(tempfile.TemporaryDirectory, 'cleanup')

    def test_happy_days(self, temp_dir_cwd):  # @UnusedVariable
        '''
        Test tempfile.TemporaryDirectory args and happy days
        '''
        root_tmp_dir = Path('tmp')
        root_tmp_dir.mkdir()
        with path_.TemporaryDirectory('suffix', 'prefix', root_tmp_dir) as tmp_dir:
            assert tmp_dir.is_dir()  # it's a Path, it's a dir
            assert tmp_dir.name.startswith('prefix')
            assert tmp_dir.name.endswith('suffix')
        assert not tmp_dir.exists()

    def test_ignore(self, temp_dir_cwd, cleanup):  # @UnusedVariable
        '''
        Test on_error=ignore
        '''
        # Ignore ENOTEMPTY (we may ignore more in the future)
        cleanup.side_effect = OSError(errno.ENOTEMPTY, 'Error msg')
        with path_.TemporaryDirectory():
            pass

        # But do raise everything else
        cleanup.side_effect = OSError(errno.ECONNABORTED, 'Error msg')
        with pytest.raises(OSError):
            with path_.TemporaryDirectory():
                pass

    def test_raise(self, temp_dir_cwd, cleanup):  # @UnusedVariable
        '''
        Test on_error=raise
        '''
        # Let any OSError through
        cleanup.side_effect = OSError(errno.ENOTEMPTY, 'Error msg')
        with pytest.raises(OSError):
            with path_.TemporaryDirectory(on_error='raise'):
                pass

def is_descendant_parameters():
    # descendant != ancestor
    parameters = [
        # descendant, ancestor, expected=True

        # Relative paths only!
        (Path('a/b'), Path('a')),
        # Use of .
        (Path('a/./b'), Path('a')),
        (Path('a/b'), Path('a/.')),
        # Use of ..
        (Path('a/b'), Path('a/b/..')),
        (Path('a/b'), Path('a/../a')),
        (Path('a/../a/b'), Path('a')),
    ]

    # Add is_descendant and expected
    parameters = [
        (is_descendant, descendant, ancestor, True)
        for is_descendant in (path_.is_descendant, path_.is_descendant_or_self)
        for descendant, ancestor in parameters
    ]

    # Add with descendant and ancestor swapped
    parameters.extend(
        (is_descendant, ancestor, descendant, False)
        for is_descendant, descendant, ancestor, _ in parameters[:]
    )

    # descendant == ancestor
    self_parameters = [
        # Relative paths only!
        (Path('a/b'), Path('a/b')),
        # Use of .
        (Path('a/./b'), Path('a/b')),
        (Path('a/b'), Path('a/b/.')),
        # Use of ..
        (Path('a/b'), Path('a/b/c/..')),
        (Path('a/b/../b'), Path('a/b')),
    ]
    self_parameters = [
        (is_descendant, descendant, ancestor, expected)
        for descendant, ancestor in self_parameters
        for is_descendant, expected in (
            (path_.is_descendant, False),
            (path_.is_descendant_or_self, True)
        )
    ]

    # Add self parameters
    parameters.extend(self_parameters)

    return parameters

@pytest.mark.parametrize('is_descendant, descendant, ancestor, expected', is_descendant_parameters())
def test_is_descendant(is_descendant, ancestor, descendant, expected):
    '''
    Test is_descendant*
    '''
    os.makedirs(str(ancestor), exist_ok=True)
    os.makedirs(str(descendant), exist_ok=True)
    assert is_descendant(descendant, ancestor) == expected
