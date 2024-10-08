-- summarize source IP and timestamps
drop view if exists response_summary;
create view response_summary as
select distinct concat_ws('_', svp.responseid, svp.ipaddress) as rsid,
       surveyid,
       min(svp.timestamp_add) as ts_start,
       max(svp.timestamp_add) as ts_end,
       (max(svp.timestamp_add) - min(svp.timestamp_add)) as duration,
	   svp.responseid as responseid,
       svp.ipaddress as ipaddr,
       count(*) as recordct
	from pio_surveypoint svp
	group by svp.surveyid, svp.responseid, svp.ipaddress
	order by ts_start;

grant select on response_summary to geodjango;

