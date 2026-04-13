RUN_SUMMARY_SQL = """
select r.id as run_id, r.project_id, r.conversation_id,
(select count(*) from drafting_section_drafts d where d.run_id = r.id) as section_count,
(select count(distinct source_id) from drafting_section_evidence e
 where e.run_id = r.id) as source_count,
(select count(distinct chunk_id) from drafting_section_evidence e
 where e.run_id = r.id) as chunk_count,
(select count(*) from evaluation_claims c where c.run_id = r.id) as claim_count,
(select count(*) from evaluation_issues i where i.run_id = r.id) as issue_count,
(select count(*) from repair_results rr
 where rr.run_id = r.id and rr.changed = 1) as repaired_section_count,
(select count(*) from repair_results rr
 where rr.run_id = r.id and rr.status != 'completed') as unresolved_section_count,
(select id from evaluation_passes ep
 where ep.run_id = r.id order by pass_index desc limit 1) as latest_evaluation_pass_id,
(select id from repair_passes rp
 where rp.run_id = r.id order by pass_index desc limit 1) as latest_repair_pass_id,
(select count(*) from artifacts a where a.run_id = r.id) as artifact_count
from runs r where r.tenant_id = :tenant_id and r.id = :run_id
"""

SECTION_SUMMARIES_SQL = """
select d.section_id, d.title, d.section_order,
exists(select 1 from repair_results rr
 where rr.run_id = d.run_id and rr.section_id = d.section_id and rr.changed = 1) as repaired,
(select count(*) from evaluation_issues i
 where i.run_id = d.run_id and i.section_id = d.section_id) as issue_count
from drafting_section_drafts d where d.run_id = :run_id order by d.section_order asc
"""

SECTION_TRACE_SQL = """
select d.section_id, d.title, d.section_order,
coalesce(case when rr.changed = 1 then rr.revised_text end, d.section_text) as canonical_text,
coalesce(
 case when rr.changed = 1 then rr.revised_summary end,
 d.section_summary
) as canonical_summary,
case when rr.changed = 1 then 1 else 0 end as repaired, rr.id as repair_result_id,
(select es.id from evaluation_section_results es
 where es.run_id = d.run_id and es.section_id = d.section_id
 order by es.created_at desc limit 1) as evaluation_result_id
from drafting_section_drafts d
left join repair_results rr on rr.id = (
 select x.id from repair_results x
 where x.run_id = d.run_id and x.section_id = d.section_id
 order by x.created_at desc limit 1
)
where d.tenant_id = :tenant_id and d.run_id = :run_id and d.section_id = :section_id
"""

SECTION_CLAIMS_SQL = """
select c.id as claim_id, c.claim_index, c.claim_text,
(select i.verdict from evaluation_issues i where i.claim_id = c.id limit 1) as verdict
from evaluation_claims c
where c.tenant_id = :tenant_id and c.run_id = :run_id and c.section_id = :section_id
order by c.claim_index asc
"""

SECTION_ISSUES_SQL = """
select i.id as issue_id, i.claim_id, i.issue_type, i.severity, i.verdict, i.message, i.rationale,
i.repair_hint, i.cited_chunk_ids_json, i.supported_chunk_ids_json, i.allowed_chunk_ids_json
from evaluation_issues i
where i.tenant_id = :tenant_id and i.run_id = :run_id and i.section_id = :section_id
order by i.claim_index asc, i.id asc
"""

SECTION_CHUNKS_SQL = """
select e.chunk_id, e.source_id, e.source_title, e.chunk_index, e.excerpt_text
from drafting_section_evidence e join drafting_section_drafts d on d.id = e.section_row_id
where e.tenant_id = :tenant_id and e.run_id = :run_id and d.section_id = :section_id
order by e.source_rank asc, e.chunk_index asc
"""

SECTION_SOURCES_SQL = """
select distinct s.id as source_id, s.canonical_key, s.title, s.identifiers_json
from retrieval_sources s join drafting_section_evidence e on e.source_id = s.id
join drafting_section_drafts d on d.id = e.section_row_id
where e.tenant_id = :tenant_id and e.run_id = :run_id and d.section_id = :section_id
order by s.title asc
"""

CHUNK_DETAIL_SQL = """
select c.id as chunk_id, c.snapshot_id, c.chunk_index, c.text, snap.source_id,
s.title, s.identifiers_json, s.metadata_json
from retrieval_source_chunks c join retrieval_source_snapshots snap on snap.id = c.snapshot_id
join retrieval_sources s on s.id = snap.source_id
where c.id = :chunk_id
and exists(
    select 1 from drafting_section_evidence e
    where e.tenant_id = :tenant_id and e.chunk_id = c.id
)
"""

CHUNK_CONTEXT_SQL = """
select c.id as chunk_id, snap.source_id, s.title as source_title,
c.chunk_index, c.text as excerpt_text
from retrieval_source_chunks c join retrieval_source_snapshots snap on snap.id = c.snapshot_id
join retrieval_sources s on s.id = snap.source_id
where c.snapshot_id = :snapshot_id and c.chunk_index between :start and :end order by c.chunk_index
"""

CHUNK_USAGE_SQL = """
select distinct e.run_id, d.section_id from drafting_section_evidence e
join drafting_section_drafts d on d.id = e.section_row_id
where e.tenant_id = :tenant_id and e.chunk_id = :chunk_id
"""

SOURCE_DETAIL_SQL = """
select s.id as source_id, s.canonical_key, s.title, s.identifiers_json, s.metadata_json,
(select count(distinct rrs.run_id) from run_retrieval_sources rrs
 join runs r on r.id = rrs.run_id
 where r.tenant_id = :tenant_id and rrs.source_id = s.id) as run_usage_count
from retrieval_sources s where s.id = :source_id
and exists(
    select 1 from run_retrieval_sources rrs join runs r on r.id = rrs.run_id
    where r.tenant_id = :tenant_id and rrs.source_id = s.id
)
"""
