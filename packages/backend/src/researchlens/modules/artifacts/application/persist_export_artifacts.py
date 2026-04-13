import json

from researchlens.modules.artifacts.application.build_export_manifest import build_manifest_json
from researchlens.modules.artifacts.application.ports import ArtifactRepository, ArtifactStorage
from researchlens.modules.artifacts.application.render_report_markdown import render_report_markdown
from researchlens.modules.artifacts.domain.artifact_kind import ArtifactKind
from researchlens.modules.artifacts.domain.export_models import (
    PersistedArtifact,
    RenderedArtifact,
    ReportExportBundle,
)


class PersistExportArtifactsUseCase:
    def __init__(self, *, repository: ArtifactRepository, storage: ArtifactStorage) -> None:
        self._repository = repository
        self._storage = storage

    async def execute(self, *, bundle: ReportExportBundle) -> tuple[PersistedArtifact, ...]:
        persisted: list[PersistedArtifact] = []
        markdown = await self._persist_one(bundle=bundle, artifact=render_report_markdown(bundle))
        persisted.append(markdown)
        manifest_json = _with_artifacts(build_manifest_json(bundle), persisted)
        manifest_artifact = await self._persist_one(
            bundle=bundle,
            artifact=_render_manifest(bundle=bundle, manifest_json=manifest_json),
        )
        persisted.append(manifest_artifact)
        manifest = await self._repository.upsert_manifest(
            bundle=bundle,
            artifact_ids=tuple(item.id for item in persisted),
            manifest_json=manifest_json,
        )
        await self._repository.attach_manifest(
            run_id=bundle.run_id,
            manifest_artifact_id=manifest_artifact.id,
            manifest_id=manifest.id,
        )
        return tuple(persisted)

    async def _persist_one(
        self,
        *,
        bundle: ReportExportBundle,
        artifact: RenderedArtifact,
    ) -> PersistedArtifact:
        storage_key = _storage_key(bundle=bundle, artifact=artifact)
        stored = await self._storage.write(storage_key=storage_key, content=artifact.content)
        return await self._repository.upsert_artifact(
            bundle=bundle,
            artifact=artifact,
            stored=stored,
        )


def _with_artifacts(
    manifest_json: dict[str, object],
    artifacts: list[PersistedArtifact],
) -> dict[str, object]:
    return {
        **manifest_json,
        "artifacts": [
            {
                "artifact_id": str(artifact.id),
                "kind": artifact.kind,
                "filename": artifact.filename,
                "media_type": artifact.media_type,
                "byte_size": artifact.byte_size,
                "sha256": artifact.sha256,
            }
            for artifact in artifacts
        ],
    }


def _render_manifest(
    *,
    bundle: ReportExportBundle,
    manifest_json: dict[str, object],
) -> RenderedArtifact:
    content = json.dumps(manifest_json, indent=2, sort_keys=True).encode("utf-8")
    return RenderedArtifact(
        kind=ArtifactKind.REPORT_MANIFEST.value,
        filename=f"run-{bundle.run_id}-manifest.json",
        media_type="application/json",
        content=content,
        metadata={"report_title": bundle.report_title},
    )


def _storage_key(*, bundle: ReportExportBundle, artifact: RenderedArtifact) -> str:
    return f"{bundle.tenant_id}/{bundle.run_id}/{artifact.kind}/{artifact.filename}"
