#!/bin/bash

#
# USAGE
# travis_run_tests.sh VERSION DB_NAME [dependency_repo_1...]

version=$1
database=$2
root_module=$3
shift 3

case ${version} in 
    7.0)
        options="--test-enable"
        ;;
    6.1)
        options=""
        ;;
    *)
        options=""
        ;;
esac

addons_path=/usr/share/pyshared/openerp/addons

for repo in "$@" $TRAVIS_BUILD_DIR; 
do
    addons_path=${repo},${addons_path}
done


echo "working in $TRAVIS_BUILD_DIR"
ls ${TRAVIS_BUILD_DIR}
for name in $(ls ${TRAVIS_BUILD_DIR});
do
    echo "considering $name"
    stripped_name=$(echo ${name} | sed 's/_unported$//')
    if check_installable ${TRAVIS_BUILD_DIR}/${name}
    then
        if [ -v tested_addons ]
        then
            tested_addons=${name},${tested_addons}
        else
            tested_addons=$name
        fi
    else
        echo " -> probably not an addon"
    fi
done

if [ ! -v tested_addons ]
then
    echo "no addon to test"
    # should we error?
    exit 0
fi

psql -c "create database ${database} with owner openerp;" -U postgres
# setup the base module without running th
/usr/bin/openerp-server --db_user=openerp --db_password=admin -d ${database} --addons-path=${addons_path} --stop-after-init -i ${root_module}

touch stdout.log
IFS=',' read -a array <<< "${tested_addons}"
for current in "${array[@]}"
do
    echo "Create DB to test ${current} -> createdb openerp_current_test --template=${database} -O openerp -U postgres"
    createdb openerp_current_test --template=${database} -O openerp -U postgres
    command="/usr/bin/openerp-server --db_user=openerp --db_password=admin -d openerp_current_test ${options} \
    --stop-after-init  --log-level test \
    --addons-path=${addons_path} \
    --init=${current}"

    echo ${command}
    coverage run $command | tee --append stdout.log
    echo "Drop DB after tests of ${current} -> dropdb openerp_current_test -U postgres"
    dropdb openerp_current_test -U postgres
done
if $(grep -v mail stdout.log | grep -q "At least one test failed when loading the modules.")
then
    exit 1
else
    exit 0
fi

