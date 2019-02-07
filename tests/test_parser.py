# Copyright (C) 2019  Jay Kamat <jaygkamat@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from jmatrix import ublock_parser, rule


MATRIX_OFF_TESTS = {
	"matrix-off: chrome-scheme true": {"chrome-scheme": {rule.Flag.MATRIX_OFF: True}},
	"\tmatrix-off:\tchrome-scheme\ttrue\t": {"chrome-scheme": {rule.Flag.MATRIX_OFF: True}},
	"matrix-off: qute-scheme false": {"qute-scheme": {rule.Flag.MATRIX_OFF: False}},
	"https-strict: qute-scheme true": {"qute-scheme": {rule.Flag.HTTPS_STRICT: True}},
	"https-strict: qute-scheme false": {"qute-scheme": {rule.Flag.HTTPS_STRICT: False}},
}

MATRIX_RULE_TESTS = {
	"* * * block": {"*": {"*": {rule.Type.ALL: rule.Action.BLOCK}}},
	"* reddit.org * allow": {"*": {"reddit.org": {rule.Type.ALL: rule.Action.ALLOW}}},
	"qutebrowser.org qutebrowser.org * inherit": {"qutebrowser.org": {"qutebrowser.org": {rule.Type.ALL: rule.Action.INHERIT}}},
	"foo.org bar.org xhr allow": {"foo.org": {"bar.org": {rule.Type.XHR: rule.Action.ALLOW}}},
	"* *": {"*": {"*": {rule.Type.ALL: rule.Action.ALLOW}}},
	"* * *": {"*": {"*": {rule.Type.ALL: rule.Action.ALLOW}}},
}

@pytest.mark.parametrize(('r', 'result'), MATRIX_OFF_TESTS.items())
def test_matrix_off(r, result):
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map([r], rule_obj)
	assert rule_obj.matrix_flags == result


@pytest.mark.parametrize(('r', 'result'), MATRIX_RULE_TESTS.items())
def test_matrix_rule(r, result):
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map([r], rule_obj)
	assert rule_obj.matrix_rules == result

@pytest.mark.parametrize(('r', 'result'), MATRIX_OFF_TESTS.items())
def test_matrix_off_serialize(r, result):
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map([r], rule_obj)
	lines = ublock_parser.map_to_rules(rule_obj)
	assert lines.split() == r.strip().lower().split()


@pytest.mark.parametrize(('r', 'result'), MATRIX_RULE_TESTS.items())
def test_matrix_rule_serialize(r, result):
	if "block" not in r and "allow" not in r:
		# the serialize doesn't leave "allow" off
		return
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map([r], rule_obj)
	lines = ublock_parser.map_to_rules(rule_obj)
	assert lines == r
