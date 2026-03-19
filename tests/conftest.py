"""Shared pytest fixtures."""

import pytest
import boxcraft as bc
from boxcraft.testing import UniformGenerator, GaussianGenerator


@pytest.fixture
def uniform_100():
    return UniformGenerator(n=100, seed=0).generate()


@pytest.fixture
def uniform_1000():
    return UniformGenerator(n=1000, seed=0).generate()


@pytest.fixture
def gaussian_100():
    return GaussianGenerator(n=100, seed=0).generate()


@pytest.fixture
def gaussian_1000():
    return GaussianGenerator(n=1000, seed=0).generate()
