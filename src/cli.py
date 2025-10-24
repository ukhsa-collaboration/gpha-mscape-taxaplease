import json
import argparse
from taxaplease import TaxaPlease
from taxaplease import __version__ as tpVersion


def init_argparser():
    parser = argparse.ArgumentParser(
        prog="taxaplease",
        description="A tool for wrangling NCBI taxonomy.",
        epilog="Subcommands have their own help available with -h",
    )

    ## subparsers are mutually exclusive by default
    subparsers = parser.add_subparsers(required=True, dest="subcommand")
    parser_taxid = subparsers.add_parser("taxid", help="Return a taxid")
    parser_record = subparsers.add_parser("record", help="Return a full taxon record")
    parser_check = subparsers.add_parser("check", help="Check metadata")
    parser_version = subparsers.add_parser("version", help="Print version information")
    parser_taxonomy = subparsers.add_parser(
        "taxonomy", help="Get valid taxonomy URLs and set taxaPlease to use them"
    )

    group_taxid = parser_taxid.add_mutually_exclusive_group()
    group_record = parser_record.add_mutually_exclusive_group()
    group_check = parser_check.add_mutually_exclusive_group()
    group_taxonomy = parser_taxonomy.add_mutually_exclusive_group()

    ## taxids
    group_taxid.add_argument("--parent", help="Get the parent taxid", metavar="<taxid>")
    group_taxid.add_argument(
        "--genus", help="Get the taxid corresponding to the genus", metavar="<taxid>"
    )
    group_taxid.add_argument(
        "--species",
        help="Get the taxid corresponding to the species",
        metavar="<taxid>",
    )
    group_taxid.add_argument(
        "--superkingdom",
        help="Get the taxid corresponding to the superkingdom",
        metavar="<taxid>",
    )
    group_taxid.add_argument(
        "--parents-all", help="Get taxids for all parents", metavar="<taxid>"
    )
    group_taxid.add_argument(
        "--common",
        help="Get the taxid for the closest common parent taxon between two taxids",
        metavar="<taxid>",
        nargs=2,
    )

    ## records
    group_record.add_argument(
        "--parent", help="Get the parent record", metavar="<taxid>"
    )
    group_record.add_argument(
        "--record", help="Get the record for the input taxid", metavar="<taxid>"
    )
    group_record.add_argument(
        "--common",
        help="Get the record for the closest common parent taxon between two taxids",
        metavar="<taxid>",
        nargs=2,
    )

    ## other
    group_check.add_argument(
        "--levels-between",
        help="Check the number of levels between two taxids (JSON output)",
        metavar="<taxid>",
        nargs=2,
    )
    group_check.add_argument(
        "--graph",
        help="Display the taxonomy graph in the terminal for one or more taxids",
        metavar="<taxid>",
        nargs="*",
    )
    group_check.add_argument(
        "--is-archaea", help="Checks if taxid is an archaea", metavar="<taxid>"
    )
    group_check.add_argument(
        "--is-bacteria", help="Checks if taxid is a bacteria", metavar="<taxid>"
    )
    group_check.add_argument(
        "--is-eukaryote", help="Checks if taxid is a eukaryote", metavar="<taxid>"
    )
    group_check.add_argument(
        "--is-virus", help="Checks if taxid is a virus", metavar="<taxid>"
    )
    group_check.add_argument(
        "--is-phage", help="Checks if taxid is a phage", metavar="<taxid>"
    )
    group_check.add_argument(
        "--status",
        help="Checks if a taxid has been merged or removed",
        metavar="<taxid>",
    )
    group_check.add_argument(
        "--baltimore",
        help="Checks the Baltimore classification of a virus",
        metavar="<taxid>",
    )

    ## taxonomy
    group_taxonomy.add_argument(
        "--set",
        help="Set the URL for the taxonomy database used by taxaPlease"
    )
    group_taxonomy.add_argument(
        "--get",
        help="Get a dictionary of valid taxonomy database URLs",
        action="store_true",
    )

    return parser


def handle_taxid_request(args, taxapleaseObj):
    if args.parent:
        return taxapleaseObj.get_parent_taxid(args.parent)
    elif args.genus:
        return taxapleaseObj.get_genus_taxid(args.genus)
    elif args.species:
        return taxapleaseObj.get_species_taxid(args.species)
    elif args.superkingdom:
        return taxapleaseObj.get_superkingdom_taxid(args.superkingdom)
    elif args.parents_all:
        return taxapleaseObj.get_all_parent_taxids(args.parents_all)
    elif args.common:
        return taxapleaseObj.get_common_parent_taxid(*args.common)
    else:
        return "Usage: taxaplease taxid -h"


def handle_record_request(args, taxapleaseObj):
    if args.parent:
        return taxapleaseObj.get_parent_record(args.parent)
    elif args.record:
        return taxapleaseObj.get_record(args.record)
    elif args.common:
        return taxapleaseObj.get_common_parent_record(*args.common)
    else:
        return "Usage: taxaplease record -h"


def handle_check_request(args, taxapleaseObj):
    if args.levels_between:
        return taxapleaseObj.get_number_of_levels_between_taxa(*args.levels_between)
    elif args.is_archaea:
        return taxapleaseObj.isArchaea(args.is_archaea)
    elif args.is_bacteria:
        return taxapleaseObj.isBacteria(args.is_bacteria)
    elif args.is_eukaryote:
        return taxapleaseObj.isEukaryote(args.is_eukaryote)
    elif args.is_virus:
        return taxapleaseObj.isVirus(args.is_virus)
    elif args.is_phage:
        return taxapleaseObj.isPhage(args.is_phage)
    elif args.status:
        return taxapleaseObj.checkTaxidStatus(args.status)
    elif args.graph:
        return taxapleaseObj.print_taxonomy_graph(*args.graph)
    elif args.baltimore:
        return taxapleaseObj.get_baltimore_classification(args.baltimore)
    else:
        return "Usage: taxaplease check -h"


def handle_taxonomy_request(args, taxapleaseObj):
    if args.get:
        return taxapleaseObj.get_taxonomy_url()
    elif args.set:
        return taxapleaseObj.set_taxonomy_url(args.set)
    else:
        return "Usage: taxaplease taxonomy -h"


def main():
    args = init_argparser().parse_args()

    tp = TaxaPlease()

    result = None

    match args.subcommand:
        case "taxid":
            result = handle_taxid_request(args, tp)
        case "record":
            result = handle_record_request(args, tp)
        case "check":
            result = handle_check_request(args, tp)
        case "version":
            result = {"taxaplease_version": tpVersion}
        case "taxonomy":
            handle_taxonomy_request(args, tp)
            result = -1
        case _:
            raise Exception(f"Unknown subcommand {args.subcommand}")

    if result == -1:
        return
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
