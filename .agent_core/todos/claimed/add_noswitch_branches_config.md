---
title: Add noswitch_branches config
status: claimed
issue_id: 97
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/97
created_at: '2026-03-11T10:30:07.012057'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-03-11T10:33:55.750429'
---
Add an option in config.toml (also make sure that patch.py will work for it), that handles the noswitch_branches - currently, when onboard.py is called, we automatically switch to 'dev' branch. This doesn't work for branches that constitute 'special deployments' e.g. white labelling. So what I want is a mapping in config.toml for 'noswitch_branches' and if onboard picks up we are in one of those branches it shouldn't automatically switch over. *In stead* it should rebase off its 'parent' (so it's almost like we are in a spec/spec branch + worktree, but the assumption is not that the branch is short lived). The mapping should therefore be 'child' -> 'parent' e.g. 'company_xyz' -> 'main' - then when we onboard and we detect we are in 'company_xyz' branch, it should attempt to rebase onto 'main' as though we were working in a spec