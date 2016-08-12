currDir=$(cd "$(dirname "$0")"; pwd)

echo "为_config.yml 创建软链接"
rm -f $currDir/../_config.yml
ln -s $currDir/_config.yml $currDir/../_config.yml


echo "为source 创建软链接"
rm -f $currDir/../source
ln -s $currDir/source $currDir/../source


echo "为theme/_config.yml 创建软链接"
rm -f $currDir/../themes/next/_config.yml
ln -s $currDir/_next-theme-config.yml $currDir/../themes/next/_config.yml

