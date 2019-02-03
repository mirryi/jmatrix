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
import functools

from jmatrix import interceptor, rule, ublock_parser


WIDEN_TESTS = {
	"a.b.com": ["a.b.com", "b.com", "com", "*"],
	"start.duckduckgo.com": ["start.duckduckgo.com", "duckduckgo.com", "com", "*"],
	"": ["*"],
	"a.b.c.d.e.f": ["a.b.c.d.e.f", "b.c.d.e.f",
					"c.d.e.f", "d.e.f", "e.f", "f", "*"],
}


@pytest.mark.parametrize(('r', 'result'), WIDEN_TESTS.items())
def test_matrix_rule(r, result):
	assert interceptor._hostname_widen_list(r) == result

@pytest.mark.parametrize(('r', 'result'), WIDEN_TESTS.items())
def test_matrix_rule_benchmark(r, result, benchmark):
	benchmark(functools.partial(interceptor._hostname_widen_list, r))


# 'e2e' Tests for overall interceptor

OVERALL_TESTS = {
	("matrix-off: * true",): {"allow": [
		("gitlab.com", "http", "gitlab.com", rule.Type.IMAGE),
		("git.gitlab.com", "https", "gitlab.com", rule.Type.IMAGE),]},

	("* * * block",
	 "* * css allow",):
	{"allow": [
		("gitlab.com", "http", "gitlab.com", rule.Type.CSS),],
	 "block": [
		 ("gitlab.com", "http", "gitlab.com", rule.Type.XHR),],
	 },

	("* * * block",
	 "* * css allow",):
	{"allow": [
		("gitlab.com", "http", "gitlab.com", rule.Type.CSS),],
	 "block": [
		 ("gitlab.com", "http", "gitlab.com", rule.Type.XHR),],
	 },

	("* qutebrowser.bad * block",
	 "qutebrowser.org qutebrowser.bad * allow",):
	{"allow": [
		("qutebrowser.org", "http", "qutebrowser.bad", rule.Type.CSS),],
	 "block": [
		 ("non-qutebrowser.org", "http", "qutebrowser.bad", rule.Type.CSS),],
	 },
}


@pytest.mark.parametrize(('r_text', 'result'), OVERALL_TESTS.items())
def test_matrix_overall(r_text, result):
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map(r_text, rule_obj)
	for blocked_rule in result.get('block', []):
		args = blocked_rule + (rule_obj,)
		assert interceptor.should_block(*args)
	for passed_rule in result.get('allow', []):
		args = passed_rule + (rule_obj,)
		assert not interceptor.should_block(*args)
