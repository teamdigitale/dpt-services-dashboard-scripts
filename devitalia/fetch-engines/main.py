#!/usr/bin/env python

import argparse
import engines
from apscheduler.schedulers.blocking import BlockingScheduler

enabled_engines = ['GitHub', 'Slack', 'Forum', 'GAnalytics', 'Onboarding', 'Catalogo', 'CatalogoRegioni', 'CatalogoCategories', 'CatalogoAudiences']

def compute_stats(args):
    for engine_name in enabled_engines:
        if not args.tool or args.tool == engine_name.lower():
            computed_stats = ""
            engine_class = getattr(engines, engine_name)
            engine = engine_class(args)
            stats = engine.compute_stats()

            keyname = engine.keyname
            computed_stats += '{},{}\n'.format(keyname, ','.join(engine.metric_names))
            for stat in sorted(stats):
                computed_stats += "{}".format(stat)
                for m in engine.metric_names:
                    computed_stats += ",{}".format(stats[stat][m])
                computed_stats += "\n"

            if args.write:
                f = open("{}/{}.csv".format(args.data_dir, engine.name), "w")
                f.write(computed_stats)
                f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Program to compute statistics for developers italia")
    parser.add_argument('-s', action="store_true", dest="schedule", help="Run app scheduled job")
    parser.add_argument('-t', action="store", dest="tool", type=str, required=False, help="Tool to compute statistics for")
    parser.add_argument('-w', action="store_true", dest="write", help="Store statistics to file")
    parser.add_argument('--data_dir', action="store", dest="data_dir", type=str, help="Directory to save stats to")
    parser.add_argument('--num_threads', action="store", dest="num_threads", type=int, help="Number of threads to execute")
    parser.add_argument('--token_github', action="store", dest="token_github", type=str, help="GitHub API key")
    parser.add_argument('--token_slack', action="store", dest="token_slack", type=str, help="Slack legacy token")
    parser.add_argument('--forum_api_key', action="store", dest="forum_api_key", type=str, help="Forum API key")
    parser.add_argument('--google_wpid', action="store", dest="google_wpid", type=str, help="Google Analytics WP id")
    parser.add_argument('--google_project_id', action="store", dest="google_project_id", type=str, help="Google Analytics Project ID")
    parser.add_argument('--google_private_id', action="store", dest="google_private_id", type=str, help="Google Analytics Private ID")
    parser.add_argument('--google_private_key', action="store", dest="google_private_key", type=str, help="Google Analytics Private Key")
    parser.add_argument('--google_client_email', action="store", dest="google_client_email", type=str, help="Google Analytics Client Email")
    parser.add_argument('--google_client_id', action="store", dest="google_client_id", type=str, help="Google Analytics Client ID")
    parser.add_argument('--google_client_x509_cert_url', action="store", dest="google_client_x509_cert_url", type=str, help="Google Analytics Client X509 Cert Url")

    args = parser.parse_args()

    if args.schedule:
        scheduler = BlockingScheduler()
        scheduler.add_job(compute_stats, 'cron', args=[args], hour='03', minute='30')
        scheduler.start()
    else:
        compute_stats(args)
