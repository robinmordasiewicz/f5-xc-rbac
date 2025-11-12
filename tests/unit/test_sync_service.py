from xc_user_group_sync.sync_service import Group, GroupSyncService


class FakeRepo:
    def __init__(self):
        self.groups = {}
        self.users = set()
        self.calls = []

    def list_groups(self, namespace: str = "system"):
        return {"items": [dict(name=n, usernames=v) for n, v in self.groups.items()]}

    def list_user_roles(self, namespace: str = "system"):
        return {"items": [{"username": u} for u in self.users]}

    def create_user(self, user: dict, namespace: str = "system"):
        self.calls.append(("create_user", user))
        self.users.add(user.get("email") or user.get("username"))
        return {"username": user.get("email")}

    def create_group(self, group: dict, namespace: str = "system"):
        self.calls.append(("create_group", group))
        self.groups[group["name"]] = list(group.get("usernames", []))
        return group

    def update_group(self, name: str, group: dict, namespace: str = "system"):
        self.calls.append(("update_group", name, group))
        self.groups[name] = list(group.get("usernames", []))
        return group

    def delete_group(self, name: str, namespace: str = "system"):
        self.calls.append(("delete_group", name))
        if name in self.groups:
            del self.groups[name]


class FailingRepo(FakeRepo):
    def __init__(self, fail_create_user=False, fail_create_group=False):
        super().__init__()
        self.fail_create_user = fail_create_user
        self.fail_create_group = fail_create_group

    def create_user(self, user: dict, namespace: str = "system"):
        if self.fail_create_user:
            raise RuntimeError("user creation failed")
        return super().create_user(user, namespace=namespace)

    def create_group(self, group: dict, namespace: str = "system"):
        if self.fail_create_group:
            raise RuntimeError("group creation failed")
        return super().create_group(group, namespace=namespace)


class TransientFailRepo(FakeRepo):
    def __init__(self, fail_times=1):
        super().__init__()
        self.fail_times = fail_times
        self.attempts = 0

    def create_user(self, user: dict, namespace: str = "system"):
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise RuntimeError("transient")
        return super().create_user(user, namespace=namespace)


def test_sync_creates_user_group_and_membership_when_missing():
    repo = FakeRepo()
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="admins", users=["alice@example.com"])]
    existing = {}

    stats = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)

    # user should have been created, group created and membership applied
    assert "alice@example.com" in repo.users
    assert "admins" in repo.groups
    assert repo.groups["admins"] == ["alice@example.com"]
    assert stats.created == 1


def test_sync_is_idempotent_on_second_run():
    repo = FakeRepo()
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="devs", users=["bob@example.com"])]
    existing = {}

    # first run applies changes
    stats1 = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)
    # build existing_groups mapping from repo.list_groups response for second run
    existing_mapping = {g["name"]: g for g in repo.list_groups().get("items", [])}
    stats2 = svc.sync_groups(
        planned, existing_mapping, existing_users=None, dry_run=False
    )

    assert stats1.created == 1
    # second run should report skipped (no changes)
    assert stats2.skipped >= 1


def test_dry_run_does_not_create_anything():
    repo = FakeRepo()
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="ops", users=["carol@example.com"])]
    existing = {}

    _ = svc.sync_groups(planned, existing, existing_users=None, dry_run=True)

    # dry-run should not create users or groups
    assert "carol@example.com" not in repo.users
    assert "ops" not in repo.groups


def test_create_user_failure_skips_group_and_records_error():
    repo = FailingRepo(fail_create_user=True)
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="ops", users=["dana@example.com"])]
    existing = {}

    stats = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)

    # creation failed, group should not be created and errors incremented
    assert "ops" not in repo.groups
    assert stats.errors > 0


def test_create_group_failure_records_error():
    repo = FailingRepo(fail_create_group=True)
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="infra", users=["erin@example.com"])]
    existing = {}

    stats = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)

    # group creation failed and was recorded
    assert "infra" not in repo.groups
    assert stats.errors > 0


def test_update_group_updates_members():
    repo = FakeRepo()
    # seed existing group
    repo.groups["team"] = ["old@example.com"]
    repo.users.add("new@example.com")
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="team", users=["new@example.com"])]
    existing = {"team": {"name": "team", "usernames": ["old@example.com"]}}

    stats = svc.sync_groups(planned, existing, existing_users=repo.users, dry_run=False)

    assert stats.updated == 1
    assert repo.groups["team"] == ["new@example.com"]


def test_cleanup_orphaned_groups_deletes():
    repo = FakeRepo()
    repo.groups = {"keep": ["a@a"], "remove": ["b@b"]}
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="keep", users=["a@a"])]
    deleted = svc.cleanup_orphaned_groups(
        planned,
        {k: {"name": k, "usernames": v} for k, v in repo.groups.items()},
        dry_run=False,
    )

    assert deleted == 1
    assert "remove" not in repo.groups


def test_parse_csv_to_groups(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Email,Entitlement Display Name\n"
        'joe@example.com,"CN=admins,OU=Groups,DC=example,DC=com"\n'
    )

    svc = GroupSyncService(repository=FakeRepo())
    groups = svc.parse_csv_to_groups(str(csv_file))

    assert len(groups) == 1
    assert groups[0].name == "admins"
    assert "joe@example.com" in groups[0].users


def test_user_creation_retries_and_succeeds():
    repo = TransientFailRepo(fail_times=2)
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="retryers", users=["sam@example.com"])]
    existing = {}

    stats = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)

    assert "sam@example.com" in repo.users
    assert "retryers" in repo.groups
    assert stats.created == 1


def test_user_creation_retries_exhausted_records_error():
    repo = TransientFailRepo(fail_times=10)
    svc = GroupSyncService(repository=repo)

    planned = [Group(name="broken", users=["fail@example.com"])]
    existing = {}

    stats = svc.sync_groups(planned, existing, existing_users=None, dry_run=False)

    assert "broken" not in repo.groups
    assert stats.errors > 0
