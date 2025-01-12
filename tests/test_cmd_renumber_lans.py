import StringIO

from util import ClientCase, Group

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.conf import settings

from peeringdb_server.models import REFTAG_MAP


class TestRenumberLans(ClientCase):

    @classmethod
    def setUpTestData(cls):
        super(TestRenumberLans, cls).setUpTestData()
        call_command("pdb_generate_test_data", limit=1, commit=True)

    def test_run(self):
        """
        test a successful execution of the `pdb_renumber_lans` command
        """

        ix = REFTAG_MAP["ix"].objects.all().first()

        ixlan = ix.ixlan_set_active.all().first()

        call_command("pdb_renumber_lans", ix=1, old=u"206.223.116.0/23", new=u"206.223.110.0/23", commit=True)

        assert ixlan.ixpfx_set.get(id=1).prefix.compressed == u"206.223.110.0/23"
        assert ixlan.netixlan_set.get(id=1).ipaddr4.compressed == u"206.223.110.101"

        call_command("pdb_renumber_lans", ix=1, old=u"2001:504:0:1::/64", new=u"2001:504:0:2::/64", commit=True)

        assert ixlan.ixpfx_set.get(id=2).prefix.compressed == u"2001:504:0:2::/64"
        assert ixlan.netixlan_set.get(id=1).ipaddr6.compressed == u"2001:504:0:2::65"


    def test_skip_deleted(self):
        """
        test that `pdb_renumber_lans` command skips deleted prefixes and
        netixlans
        """

        ix = REFTAG_MAP["ix"].objects.all().first()

        ixlan = ix.ixlan_set_active.all().first()

        for ixpfx in ixlan.ixpfx_set.all():
            ixpfx.delete()

        for netixlan in ixlan.netixlan_set.all():
            netixlan.delete()


        call_command("pdb_renumber_lans", ix=1, old=u"206.223.116.0/23", new=u"206.223.110.0/23", commit=True)

        assert ixlan.ixpfx_set.get(id=1).prefix.compressed == u"206.223.116.0/23"
        assert ixlan.netixlan_set.get(id=1).ipaddr4.compressed == u"206.223.116.101"

        call_command("pdb_renumber_lans", ix=1, old=u"2001:504:0:1::/64", new=u"2001:504:0:2::/64", commit=True)

        assert ixlan.ixpfx_set.get(id=2).prefix.compressed == u"2001:504:0:1::/64"
        assert ixlan.netixlan_set.get(id=1).ipaddr6.compressed == u"2001:504:0:1::65"



    def test_ignore_diff_address_space(self):
        """"
        Test that `pdb_renumber_lans` command soft errors on netixlans that
        arent in the specified address space (but exist on the ixlan)
        """

        ix = REFTAG_MAP["ix"].objects.all().first()

        ixlan = ix.ixlan_set_active.all().first()

        out = StringIO.StringIO()

        call_command("pdb_renumber_lans", ix=1, old=u"206.223.114.0/23",
                     new=u"206.223.110.0/23", commit=True, stdout=out)

        assert ixlan.ixpfx_set.get(id=1).prefix.compressed == u"206.223.116.0/23"
        assert ixlan.netixlan_set.get(id=1).ipaddr4.compressed == u"206.223.116.101"

        output = out.getvalue()
        assert output.find("[error] 206.223.116.101: Ip address not within old prefix") > -1

        call_command("pdb_renumber_lans", ix=1, old=u"2001:504:0:3::/64",
                     new=u"2001:504:0:2::/64", commit=True, stdout=out)

        assert ixlan.ixpfx_set.get(id=2).prefix.compressed == u"2001:504:0:1::/64"
        assert ixlan.netixlan_set.get(id=1).ipaddr6.compressed == u"2001:504:0:1::65"

        output = out.getvalue()

        assert output.find("[error] 2001:504:0:1::65: Ip address not within old prefix") > -1



