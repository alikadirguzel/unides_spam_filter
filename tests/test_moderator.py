from src.filter import ContentModerator, ModerationStatus


moderator = ContentModerator.load_default()


def test_forbidden_text_rejected():
    result = moderator.moderate("sen tam bir şerefsizsin")
    assert result.status == ModerationStatus.REJECT
    assert "şerefsiz" in result.metadata["matches"]


def test_spam_requires_admin_review():
    result = moderator.moderate("bedava bonus kazanmak için hemen https://spam.test linke tıkla")
    assert result.status == ModerationStatus.ADMIN_REVIEW_SPAM
    assert result.scores["spam_rule"] >= 0.55 or result.scores["spam_model"] >= 0.6


def test_politics_goes_to_admin():
    sample = "Bu seçim manifestomuzda demokrasi ve meclis reformu var, oy verin!"
    result = moderator.moderate(sample)
    assert result.status == ModerationStatus.ADMIN_REVIEW_POLITICS
    assert "demokrasi" in result.metadata["politics_keywords"]


def test_clean_text_accepted():
    result = moderator.moderate("Bugün hava çok güzel, yürüyüşe çıkıyorum.")
    assert result.status == ModerationStatus.ACCEPT

