from src.match import Match
import pytest


@pytest.mark.parametrize(
    "path_to_test_match, expected_results",
    [
        ("tests/unit/test_data/test_match_1.json", {"walk": 3, "rest": 1}),
        (
            "tests/unit/test_data/test_match_2.json",
            {"walk": 4, "rest": 4, "run": 3, "dribble": 2},
        ),
    ],
)
def test_count_actions(path_to_test_match, expected_results):
    test_match = Match(path_to_test_match)
    assert test_match.count_actions() == expected_results


@pytest.mark.parametrize(
    "path_to_test_match, expected_results",
    [
        ("tests/unit/test_data/test_match_1.json", {"MIN": 2, "MAX": 6}),
        ("tests/unit/test_data/test_match_2.json", {"MIN": 1, "MAX": 14}),
    ],
)
def test_find_min_max(path_to_test_match, expected_results):
    test_match = Match(path_to_test_match)
    assert test_match.find_min_max() == expected_results


@pytest.mark.parametrize(
    "action, expected_results",
    [("walk", 3.203333333333333), ("rest", 3.4)],
)
def test_mean_norm_for_each_action(action, expected_results):
    test_match = Match("tests/unit/test_data/test_match_1.json")
    assert test_match.mean_norm_for_each_action(action) == expected_results


@pytest.mark.parametrize(
    "path_to_test_match, expected_results",
    [
        (
            "tests/unit/test_data/test_match_1.json",
            {"rest": 3.4, "walk": 3.203333333333333},
        )
    ],
)
def test_mean_norm_per_action(path_to_test_match, expected_results):
    test_match = Match(path_to_test_match)
    assert test_match.mean_norm_per_action == expected_results


# @pytest.mark.parametrize(
#     "path_to_test_match, expected_results",
#     [
#         (
#             "tests/unit/test_data/test_match_1.json",
#             [
#                 ["walk"],
#                 ["walk"],
#                 ['walk', 'walk', 'walk'],
#                 ['walk', 'walk', 'walk'],
#             ],
#         )
#     ],
# )
# def test_extract_sequences(path_to_test_match, expected_results):
#     test_match = Match(path_to_test_match)
#     assert test_match.extract_sequences() == expected_results


@pytest.mark.parametrize(
    "path_to_test_match, expected_results",
    [
        ("tests/unit/test_data/test_match_1.json", {"walk": 3, "rest": 6}),
        (
            "tests/unit/test_data/test_match_2.json",
            {"walk": 9, "run": 4, "rest": 11, "dribble": 3},
        ),
    ],
)
def test_average_gait_length_per_action(path_to_test_match, expected_results):
    test_match = Match(path_to_test_match)
    assert test_match.average_gait_length_per_action == expected_results


@pytest.mark.parametrize(
    "path_to_test_match, expected_results",
    [
        (
            "tests/unit/test_data/test_match_1.json",
            {"walk": {"walk": 2, "rest": 1}},
        ),
    ],
)
def test_compute_correlation(path_to_test_match, expected_results):
    test_match = Match(path_to_test_match)
    assert test_match.compute_correlation() == expected_results
