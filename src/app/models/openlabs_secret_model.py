

class OpenLabsSecretModel(Base):
    """SQLAlchemy ORM model for OpenLabs Secrets."""

    __tablename__ = "secrets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", unique=True), nullable=False)

    aws_access_key: Mapped[str] = mapped_column(String, nullable=True)
    aws_secret_key: Mapped[str] = mapped_column(String, nullable=True)
    aws_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    azure_client_id: Mapped[str] = mapped_column(String, nullable=True)
    azure_client_secret: Mapped[str] = mapped_column(String, nullable=True)
    azure_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user = relationship("OpenLabsUserModel", back_populates="secrets")
