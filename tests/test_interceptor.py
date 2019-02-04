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
		 ("gitlab.com", "http", "gitlab.com", rule.Type.XHR),],},

	("* * * block",
	 "* * css allow",):
	{"allow": [
		("gitlab.com", "http", "gitlab.com", rule.Type.CSS),],
	 "block": [
		 ("gitlab.com", "http", "gitlab.com", rule.Type.XHR),],},

	("* qutebrowser.bad * block",
	 "qutebrowser.org qutebrowser.bad * allow",):
	{"allow": [
		("qutebrowser.org", "http", "qutebrowser.bad", rule.Type.CSS),
		("sub.qutebrowser.org", "http", "qutebrowser.bad", rule.Type.CSS),
		("www.sub.qutebrowser.org", "http", "www.qutebrowser.bad", rule.Type.CSS),],
	 "block": [
		 ("non-qutebrowser.org", "http", "qutebrowser.bad", rule.Type.CSS),
		 ("non-qutebrowser.org", "http", "www.qutebrowser.bad", rule.Type.CSS),],},

	("* * frame block",
	 "github.com githubassets.com * allow",):
	{"allow": [
		("github.com", "http", "githubassets.com", rule.Type.CSS),
		("github.com", "http", "super.githubassets.com", rule.Type.CSS),
		("super.github.com", "http", "super.githubassets.com", rule.Type.CSS),
		("super.github.com", "http", "githubassets.com", rule.Type.CSS),

	],
	 "block": [
		 ("github.com", "http", "qutebrowser.org", rule.Type.CSS),
		 ("qutebrowser.org", "http", "githubassets.com", rule.Type.CSS),
		 # TODO how should we block this
		 ("github.com", "http", "githubassets.com", rule.Type.FRAME),
		 ("github.com", "http", "super.githubassets.com", rule.Type.FRAME),
		 ("super.github.com", "http", "super.githubassets.com", rule.Type.FRAME),
		 ],},

	("com * frame block",
	 "github.com githubassets.com * allow",):
	{"allow": [
		("github.com", "http", "githubassets.com", rule.Type.CSS),
		("github.com", "http", "super.githubassets.com", rule.Type.CSS),
		("super.github.com", "http", "super.githubassets.com", rule.Type.CSS),
		("super.github.com", "http", "githubassets.com", rule.Type.CSS),

	],
	 "block": [
		 ("github.com", "http", "qutebrowser.org", rule.Type.CSS),
		 ("qutebrowser.org", "http", "githubassets.com", rule.Type.CSS),
		 # TODO how should we block this
		 ("github.com", "http", "githubassets.com", rule.Type.FRAME),
		 ("github.com", "http", "super.githubassets.com", rule.Type.FRAME),
		 ("super.github.com", "http", "super.githubassets.com", rule.Type.FRAME),
		 ],},

	("* * xhr allow",
	 "github.com githubassets.com * block",):
	{"allow": [
		("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),
		("github.com", "http", "github.com", rule.Type.XHR),
		("super.github.com", "http", "github.com", rule.Type.XHR),
		("github.com", "http", "super.github.com", rule.Type.XHR),
		("super.github.com", "http", "super.github.com", rule.Type.XHR),
		("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),],
	 "block": [
		 ("github.com", "http", "githubassets.org", rule.Type.CSS),
		 ("super.github.com", "http", "super.githubassets.org", rule.Type.CSS),
		 ("qutebrowser.org", "http", "githubassets.com", rule.Type.CSS),
		 # TODO how should we block this
		 ("github.com", "http", "githubassets.com", rule.Type.XHR),
		 ("super.github.com", "http", "githubassets.com", rule.Type.XHR),
		 ("github.com", "http", "super.githubassets.com", rule.Type.XHR),
		 ("super.github.com", "http", "super.githubassets.com", rule.Type.XHR),],},

	("* * * block",
	 "* 1st-party * allow",):
	{"allow": [
		("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),
		("github.com", "http", "github.com", rule.Type.XHR),
		("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),
		("github.com", "http", "super.github.com", rule.Type.XHR),
		("super.github.com", "http", "super.github.com", rule.Type.XHR),
		("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),
		("twitch.tv", "https", "twitch.tv", rule.Type.OTHER),],
	 "block": [
		("qutebrowser.org", "http", "gitlab.com", rule.Type.XHR),],},

	("* * * block",
	 "matrix-off: qute-scheme true",):
	{"allow": [
		("version", "qute", "version", rule.Type.XHR),],
	 "block": [("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),],},


	("* * * block",
	 "matrix-off: qute-scheme true",):
	{"allow": [
		("version", "qute", "version", rule.Type.XHR),],
	 "block": [("qutebrowser.org", "http", "qutebrowser.org", rule.Type.XHR),],},
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


def test_benchmark_null_match(benchmark):
	"""Benchmarks the most complicated (ironically) match, the null match."""
	rule_obj = rule.Rules()
	ublock_parser.rules_to_map(["* * * block"], rule_obj)
	benchmark(functools.partial(
		interceptor.should_block,
		"a.b.c.d.e.f.g", "http", "cdn.a.b.c.d.e.f.g", rule.Type.FRAME, rule_obj))
