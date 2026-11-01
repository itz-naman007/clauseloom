export type Risk = 'high'|'medium'|'low';
export type Flag = {flag_id:string;severity:Risk;category:string;matched_text:string;explanation_template:string;suggestion_template:string};
export type ClauseResult = {clause:{id:string;index:number;heading:string;text:string;page:number};flags:Flag[];explanation:{plain_summary:string;who_benefits:string;risk_level:Risk;why_it_matters:string;what_to_ask_or_negotiate:string;evidence_quote:string};confidence:string;ai_available:boolean};
export type Summary = {overall_score:number;label:string;formula:string;verdict:string;counts:Record<Risk,number>;top_flags:Flag[]};
export type Info = {filename:string;doc_type:string;clause_count:number;warnings:string[];model:string};
export const weights = {high:15,medium:7,low:2};
export function filtered(clauses:ClauseResult[],search:string,risk:string,only:boolean){return clauses.filter(r=>(risk==='all'||r.explanation.risk_level===risk)&&(!only||r.flags.length>0)&&`${r.clause.text} ${r.explanation.plain_summary}`.toLowerCase().includes(search.toLowerCase()));}
