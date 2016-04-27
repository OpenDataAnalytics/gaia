--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: iraq_roads; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE iraq_roads (
    ogc_fid integer NOT NULL,
    geometry geometry(MultiLineString,4326),
    osm_id character varying,
    name character varying,
    ref character varying,
    type character varying,
    oneway integer,
    bridge integer,
    tunnel integer,
    maxspeed integer
);


--
-- Name: iraq_roads_ogc_fid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE iraq_roads_ogc_fid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: iraq_roads_ogc_fid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE iraq_roads_ogc_fid_seq OWNED BY iraq_roads.ogc_fid;


--
-- Name: ogc_fid; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY iraq_roads ALTER COLUMN ogc_fid SET DEFAULT nextval('iraq_roads_ogc_fid_seq'::regclass);


--
-- Data for Name: iraq_roads; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO iraq_roads VALUES (1, '0105000020E6100000010000000102000000110000004513831B84274640C22275F16DA5404067F915C671274640EA697693CEA540407DDB02F85D274640C7C3318111A64040DA77A0A932274640845DB9837DA64040646314BA012746405A907758F2A64040BEEA121FE92646407E3F90172DA74040FE20DCAEE12646400AA359D93EA74040D322EC25D72646402D8E6F9461A740409B649A9FD12646409FCBD42478A740407FE7CD97CD26464092B30B6190A740406E934039C026464028BA2EFCE0A740404BE82E89B32646402C05EE8A2AA84040D7112CB3AD2646402FF3C24252A84040BD303E71A52646402AE7E6768AA840401243BCBF8B26464086B542A21AA9404085A570F37C26464053F245D675A94040B6555A9077264640E75C401EB0A94040', '4061247', '', 'A86', 'bikepath', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (2, '0105000020E61000000100000001020000001400000099DEB4CF192646403A3BBE62B2AF404021D335EE2826464000F3DAB639AF40400910AA7933264640B6A569ABEDAE40409A16067646264640D19D16725BAE40407927FAD74D2646407EC6850321AE4040352F3D505D264640AE98B624ACAD40401E6CB1DB67264640F866406260AD40401B683EE76E264640750B13FC25AD4040082EA0617B264640BAFC3D67C1AC40402516421889264640706FC8505FAC4040D7254FFE93264640BF83FAF1F2AB4040772B4B7496264640F8BF7EE3C6AB40407845F0BF952646403E8D203AA9AB404073BC02D1932646407D0ADBAA7FAB4040C535E3D98A264640AEFAB72638AB4040AF473C34872646404458E8DE1EAB40405C3233D879264640831F8B23C5AA404083C4D1B073264640F23A87D79AAA4040493C8F4072264640CB9C2E8B89AA40408686C5A86B264640F0C7A30A35AA4040', '4074629', '', 'A86', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (3, '0105000020E610000001000000010200000006000000C216BB7D563246407CC509021AAE40400A641B5D4A324640496018552BAE404053FA53F4D13146403373DC84D6AE4040792E4267883146401F63EE5A42AF4040034356B77A314640C1024EA555AF4040FB39AA3F6731464056664AEB6FAF4040', '4074770', '', 'A86/N11/D383', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (4, '0105000020E61000000100000001020000000E00000079EEF3CE5732464038C7CA7910AE4040AA054026633246409A76D61302AE40402C4C3A257B3246403270E591E4AD4040B340BB438A3246405E126745D4AD404076D7231E9A32464030DFB023C4AD4040C806D2C5A63246405F402FDCB9AD40407F51DDB7B5324640E996C228ADAD40403D8D6AC7C33246403673486AA1AD4040DDA117A4CF32464017BB7D5699AD40408BCF53D3E43246400E7E874787AD40400D3BE702F23246400137E6D07DAD4040A8FAF087FA3246407C8560B076AD4040DA0649FA0F3346401A2B7B5C65AD404028493206313346405685611B4CAD4040', '4074779', '', 'A86/N11/D383', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (5, '0105000020E610000001000000010200000006000000CE1E1E786B26464076E3DD91B1B34040FC8BA03193264640C786C9AF7AB34040A6C123E0C626464054A63DCA2DB34040783F13060A2746400A4D124BCAB2404006A799492F27464030EF16ED96B24040C7B94DB857274640BD62FCEA60B24040', '4076793', '', 'A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (6, '0105000020E6100000010000000102000000110000000DC9247E20264640B07F8DDAB3AF404028CDE6711826464043797A00E6AF404001B9C49107264640AA132BFE4AB04040C3ADCCA502264640D1F1875572B04040B99BF1C7FE254640A0F76B578DB0404084A2D4B9FD254640E5411FD1A9B04040B9814C7CFF2546404A89134EC1B04040F88C446804264640745C3233D8B040400B9755D80C2646400D839E72F1B04040F4B9241818264640A7A90AB20AB140401BE8EB43282646400FDE0D5828B140402127A7D13F264640DC61B8DF46B140405772BAD16C264640AC4CF8A57EB14040A58059468F264640544DB5BBACB1404015E69887A7264640BAFF7EE7CDB14040380DF6CBCC264640866CC5A3F9B140405CA49AA3D8264640D25C024B09B24040', '4076776', '', 'A862', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (7, '0105000020E610000001000000010200000012000000D82C978DCE264640EEA0C84917B24040F8E75894C82646401A1538D906B24040A6D24F38BB264640449C983FF0B14040A1C7DE41A226464001D41E40D0B14040317C444C8926464052CB7B41B0B140407847212466264640ACCABE2B82B140400DE94BCA38264640342B80CE49B140403CBD52962126464044BD851A2AB140404BD6975B102646402FE301C00CB140402CA006C20426464084C76DEAF2B040401A96F551FC254640745C3233D8B040400F841A74F8254640F72E9402C1B04040707E1EFEF5254640E5411FD1A9B04040A691E057F6254640054713398EB040404597DCCDF8254640C0FC5FBF71B04040578748F201264640EC7882B34AB040407FCFB46911264640F01EFBB4E5AF404099DEB4CF192646403A3BBE62B2AF4040', '4076777', '', 'A862', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (8, '0105000020E61000000100000001020000001200000015E69887A7264640BAFF7EE7CDB14040DCFFB6DDBA264640957C9175DDB14040F801FEDFC7264640E1506452E8B14040E10A28D4D32646405491C0D5F0B14040FF40B96DDF264640ED3DA6FFF6B14040864FDFD7ED26464073F56393FCB140406E3E6480FA26464071732A1900B24040C187B773062746400BA249BD02B24040BDB497231A274640A4D0686105B2404066E31CD02D27464037FA980F08B24040EE43392C6827464034F6251B0FB24040B55D57827B274640ACBC2E0D0DB240403374475A852746405BE4E83B09B24040509033A8912746405EE85B3002B2404039B302E89C274640C8BDAF80F8B14040E1C4A1C8A4274640321D3A3DEFB1404095DAE621AE2746403819B03FE4B140404044B467E02746400DE36E10ADB14040', '4076778', '', 'A862/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (9, '0105000020E610000001000000010200000007000000D0CB28965B27464086014BAE62B24040609A33EC41274640140DADA987B24040DA8B0D82332746401C78B5DC99B24040813749980E27464091860959CCB24040E5CC1BCCCB26464054A63DCA2DB34040A1B6B2E9AD264640D1274DDE5BB340406159C40B7D264640D04543C6A3B34040', '4076792', '', 'A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (10, '0105000020E610000001000000010200000010000000609A33EC41274640140DADA987B24040F182E38D27274640BE11DDB3AEB24040475167EE21274640FF5FD09DBBB24040A84B6B781F274640DB5E1CA6C7B240407E7ECE93212746406094A0BFD0B24040BD89C67F26274640E64B5E53D6B24040C66757C62B274640A264CD23DAB24040D971683634274640D152C3C8DCB2404058A2FD593D274640A0E293A9DDB240400ACCAF8B472746402A9EC431DCB2404014AA40D24C2746406E855561D8B2404081898917552746404ECD8A4DD0B24040EA7BC33357274640C715CDB9CAB24040218F858D572746403069E78FC4B24040EB95687F56274640227832EEBCB2404078915385502746402A8018D7AEB24040', '4076794', '', '', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (11, '0105000020E610000001000000010200000008000000CE1E1E786B26464076E3DD91B1B340408C40063C7A264640053C1F5498B340407463D57B85264640E76CA6E782B34040FB57569A9426464042E66FE767B34040EEA6A503A32646404783802150B34040CDB79965AA26464007358D3743B34040EAB9E067B72646402E3AB42330B34040BE9E54A0BB264640CF70B9B024B34040', '4076799', '', 'A862/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (12, '0105000020E6100000010000000102000000130000006A5A18D819274640BB42C472F0B2404017450F7C0C274640FD12F1D6F9B24040512BF125F9264640B4A5B33808B34040FEFB427EEC264640AF1F07CA12B340404BEC3598E126464026CFABF01DB3404059EBD511D1264640402FDCB930B340406159C40B7D264640D04543C6A3B34040E72F99CF5E264640C40B2252D3B34040CED5A0794A26464069FD2D01F8B3404077CA598E4626464066F9BA0CFFB340409DC0CF132A264640C1FB4FA335B44040378710FC14264640F113628962B44040E58BACEB06264640CA79104C7FB44040142C6920F12546402F06C545A4B44040572426A8E12546404C530438BDB44040B2F913F0C6254640F6B3588AE4B44040EBC5504EB42546406BCA5F6B00B54040FE97101890254640686ECF3D35B54040DB560E886B254640588C5F1D6CB54040', '4076800', '', 'A862/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (13, '0105000020E610000001000000010200000014000000B7F1272A1B2F4640603C8386FEA540404E51E4FF442F4640F60A0BEE07A6404007A0AC73672F464013138A6313A6404080C9D7AF852F46407380608E1EA64040C4DF4092A32F46403E2E60B829A640403E3DB665C02F4640673A85A636A6404024BF34FBF22F4640A33616B94CA64040C29668DA0F30464014AD815259A64040E11EF065473046409C267D6B71A640406692472696304640A3E47A8093A64040FDF103FCBF3046407B270B04A6A6404044C6FE0D353146403E2FCB8DD8A640407890E8AFA13146406DF9ED9007A74040AF134D56FB31464046D8A66730A74040DC662AC4233246405ABD1EA743A74040D2A645D84B3246403E3267C757A740401A1A05775632464088A361E75CA740405A0B58175C324640A69C2FF65EA740403892150D6332464058A3C3E85EA74040B86702EA72324640A0DFF76F5EA74040', '4081165', '', 'A861', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (14, '0105000020E610000001000000010200000014000000022E235058324640A0D10C9876A740401A1A057756324640FA0560A868A740407C14090154324640146E43D664A740400882B68B1F324640E6374C3448A740401028F62BF8314640E519EA6635A74040B6813B50A7314640D45D7E4C10A740406D6468869E3146402321DB430CA740404C95DEED303146403C37C87FDCA6404040D01B38B1304640C37DE4D6A4A6404091932EA2923046402F3196E997A64040772CB649453046404159428875A64040EE974F560C3046400C3AC6BA5DA640409EEDD11BEE2F46405317957950A640409E37BAEFBD2F4640B221495A3BA64040BACD65B49F2F46408815246C2EA64040ABB019E0822F464006BEFD1422A6404060617770662F4640CF81E50819A6404068CEFA94632F4640D672672618A6404079382630422F464063DC1ECE0DA640408212B067192F464058C9C7EE02A64040', '4081166', '', 'A861', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (15, '0105000020E61000000100000001020000000B000000F0344F649C28464056760B6EB5B04040DF4C4C176228464003ED0E2906B1404081E5AD5F55284640FA62EFC517B14040D7998C74502846404FD257EB1FB140401E43119C442846409F7994A531B1404081D9F3EB3D28464048A5D8D138B1404007A2DDD7372846405C1146FD3FB1404057FF8C77EC274640223E6656A5B14040493CEAF9E427464053B70E69AFB14040E4CE96BDB6274640DB9B29BEEBB14040D0CB28965B27464086014BAE62B24040', '4234529', '', 'A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (16, '0105000020E610000001000000010200000006000000C7B94DB857274640BD62FCEA60B240404044B467E02746400DE36E10ADB14040AC3DA2F8E72746405FECBDF8A2B14040FDA9A74533284640E6CC76853EB1404077E1BD59392846407F068A0E37B14040983567333D284640AE2589CA2BB14040', '4234530', '', 'A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (17, '0105000020E61000000100000001020000002F0000008C2FDAE3852846405A8F0C8343B14040CA8C124FD1284640A417B5FB55B1404084A7469EDA284640A2DD32F158B1404040A0D8AFE028464084BE4FB05AB140403FA31930ED284640F92AF9D85DB14040511AC5CD04294640C141D6AE64B140407F99396E42294640592B7F6374B1404098E2056C62294640CC6BDBE67CB1404008FA55CA7C294640412E71E481B14040424CD3B194294640750DE9A683B140403F79B361A8294640412E71E481B14040FB80F6D9B7294640960A2AAA7EB140404D7C5AEAC52946404432E4D87AB140407EA257A8DA294640254C07A172B1404010F7A287EB294640E86C5C5A68B1404075DC3A49042A4640CF5A1B7453B14040A235502A2B2A46409FBB13A232B14040116745D4442A4640417452A923B140408F7D35AC4E2A4640855BE3D81FB1404083B2DFC95D2A4640228E75711BB140400AC105346C2A4640E2AA573618B1404027C34C36792A46409CD6B7DD15B140404F0BB9AD882A4640378710FC14B14040A68F0AAD982A46404F3FA88B14B140403C1F5498AD2A4640487C389215B140400D7F9763C32A46409A547E6319B140400EB7E809F02A4640C72B103D29B140400F09DFFB1B2B46402573D13538B140401AB7E22C362B4640E44A3D0B42B14040B56B425A632B4640376046674FB14040DD990986732B464058C85C1954B1404065C2D43B812B4640E001542756B14040C1CF132A932B4640793073CB58B14040E7E3350AA42B4640CC8AF21659B140407026A60BB12B46405646239F57B140400047A753C32B4640056EDDCD53B140406766C11FD92B4640C01B77EF4DB140402D663A2AED2B4640C41FEAE346B14040807B4386FA2B464074C9DD8C3FB1404007BEB387072C46408B44B29135B140403A7716180D2C4640A5AC95BF31B1404085BAFE13122C4640070F2E782CB140400DC9247E202C4640FEA325451AB14040B20DDC813A2C46407CF88D0AF7B04040AE3ABC314E2C464025B9B2FAD9B04040FFBC5FBB6A2C4640E0032AD2B3B040408B2320706E2C464083F92B64AEB04040', '4234531', '', 'A432', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (18, '0105000020E610000001000000010200000009000000F1DA00C7F9284640BFA4E7CC2CAA40408DDA58E4322946405829F34531AA4040C17861C66F2946403FC7478B33AA4040B02CE285BE294640B50B170335AA4040335F6FACD5294640865968E734AA4040A1FE0EA03A2A4640A416EF6C34AA404051A79773842A4640DA77A0A932AA4040FFAF3A72A42A464022CE797C31AA40404939A979D82A46405BB164332CAA4040', '4234564', '', 'A14', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (19, '0105000020E6100000010000000102000000090000009C734B06DB2A46402453F4763AAA40400E315EF3AA2A46404D8AEA083BAA404050734DDC852A4640D082AB973AAA4040A118B4EB392A46409A21FA5A3CAA4040CF296D16D429464016855D143DAA404046065ED2BD294640FE70A13C3DAA4040F7A5C86B6F294640882CD2C43BAA4040A14E2FE708294640A20A7F8637AA404045AB49A6F92846407FAA65C636AA4040', '4234565', '', 'A14', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (20, '0105000020E61000000100000001020000000900000045AB49A6F92846407FAA65C636AA40407347FFCBB52846403FC7478B33AA4040C78B3B9457284640F661BD512BAA40406C75DE6BAD274640C8E64FC01BAA4040A39410ACAA264640350D8AE601AA4040B01EF7ADD6254640FE0FB056EDA9404093F9EC253225464035E4E9A6DEA940401C3746FCD424464021E010AAD4A94040CB6A15585B244640BC81B861CAA94040', '4234574', '', 'A14', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (21, '0105000020E610000001000000010200000003000000B14813EF0031464009658632F9AF4040E0D8B3E73231464023BDA8DDAFAF40404B1DE4F5603146407BA4C16D6DAF4040', '4289927', '', 'A86', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (22, '0105000020E610000001000000010200000003000000FB39AA3F6731464056664AEB6FAF40401EB0613C39314640ABF69FEBB1AF4040015DA0490731464038E3EAB6FAAF4040', '4289928', '', 'A86/N11/D383;A86', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (23, '0105000020E6100000010000000102000000170000006B11AC05512E464057467E58CAB340406BF706BA512E464019FCFD62B6B340400B17A87B532E4640A650CC30A4B34040A9E8595A572E464032A59AFE91B34040531AD6F95C2E46408A1AF1097EB34040FCFD62B6642E4640A1AC29DA66B34040DB28FC636B2E4640C72F174C57B34040B939F0C5722E4640109D54EA48B340406D63A2F77C2E4640F63C242136B34040AF473C34872E4640F2F8AC2127B34040C385973B8E2E464027EF88AF1BB340400B6F206E982E46408251EEE30DB34040FD892540A82E4640A95615D0FAB24040C3BDE8E1BA2E46406E8ECE54E3B240402AF7A7F9CF2E46403F4C67CCC9B24040ED3DA6FFF62E464029CA4A3899B2404089A8D3CB392F4640F9FE61A648B24040A816B60B722F46403920AE4104B24040F7A68EFA902F4640761B2F38DEB140404A129557F82F4640880DBB945FB14040827B54B252304640A5541DCDECB0404024E6FE8FB8304640EE0CAE145DB04040B14813EF0031464009658632F9AF4040', '4289929', '', 'A86/A862', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (24, '0105000020E610000001000000010200000017000000015DA0490731464038E3EAB6FAAF404003F7F2F1BF30464011F7FD405EB04040618C48145A3046403E833C71EFB040408AE942ACFE2F4640CEE15AED61B14040367E3C4F972F4640C3B23E8ADFB140400D665DED722F4640BE55325B0DB24040928664123F2F4640922D814A4BB240408C0F58DEFA2E46403D7E6FD39FB2404069CE554ED62E4640D97A8670CCB2404038C2FDDBC02E46409C7CC4F9E5B24040A7BBA1DFAD2E464043853474FDB24040B586F7C19E2E46400A8BE5F10FB34040378AAC35942E4640AF2880BD1DB34040575F13888D2E46405748540328B34040E167B7F1822E46406C81F39837B340402D3E05C0782E4640AACB738E4BB340404F2D115E712E46400E04B7A459B34040DB28FC636B2E4640D68BA19C68B340409B1D0478662E464029CFBC1C76B3404028FF4932612E4640BAF5F5D786B340401E0714A05C2E46407475C7629BB34040B414DA835A2E4640A24C593CABB34040DFFB1BB4572E4640F47810F1C5B34040', '4289930', '', 'A82/A862', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (25, '0105000020E61000000100000001020000000C000000D67AD0FDE626464047AF06280DAA4040891E42A6C626464047AF06280DAA40400B22F719BC264640E25F5F460CAA4040F717E6A9B3264640AC80E7830AAA40400FF5166AA8264640094E226706AA4040BDF9B2599A264640073F7100FDA94040D88F5E1E7C26464099D134CDE0A940409A9E0B7E76264640EB1C03B2D7A940408FA6D5EB712646408FC250E2CEA94040269AF68370264640475DC6A8C6A94040F086342A70264640D00946CABBA940405BADB8DD702646408F177728AFA94040', '4345579', '', '', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (26, '0105000020E6100000010000000102000000040000006C75DE6BAD274640C8E64FC01BAA4040CC0FB79E7C274640FF4701FD19AA4040D0F23CB83B2746402BC5E97F14AA4040D67AD0FDE626464047AF06280DAA4040', '4345580', '', '', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (27, '0105000020E6100000010000000102000000030000005BADB8DD702646408F177728AFA940409984663277264640D5264EEE77A9404091D26C1E87264640BFD76BD509A94040', '4345581', '', 'A86', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (28, '0105000020E61000000100000001020000001000000047BBC09B24254640A1979BB9D1A94040F39CE392992546404298DBBDDCA94040F9DB9E20B1254640B8DCAA35DEA940407105CA5CCF25464010786000E1A94040E3D2E759FF2546406C544C4AE6A940408DD8DDF247264640EC1A88C0ECA94040519BDDFF6C264640C74CA25EF0A940407A1B9B1DA926464023298EA8F5A94040869D1848062746407E834078FEA9404021D0F46D1C2746405917B7D100AA40400FB40243562746401A434AFD06AA40409776C5E7A9274640FD38509610AA404042B9C898162846403A741F251BAA4040C78B3B945728464059A2B3CC22AA40406737E96CB7284640329A4B6029AA4040F1DA00C7F9284640BFA4E7CC2CAA4040', '4345629', '', '', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (29, '0105000020E610000001000000010200000009000000BE9E54A0BB264640CF70B9B024B34040FDDD9623BF264640F3716DA818B3404033D7B331C0264640E702F2800DB3404007BC276AC426464006B47405DBB24040B0D3FEBDCA26464022FE614B8FB240408FFE976BD1264640821CEFE945B2404076FE486CD22646408D367D2C33B24040AC2BB011D226464041E4E3C924B24040D82C978DCE264640EEA0C84917B24040', '4447807', '', 'A862/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (30, '0105000020E61000000100000001020000000400000035994C7045274640464BD4C1B0B24040C29437763F2746407422669BC0B2404006966DF13A2746401C00BBE4C9B240403E93FDF33427464076E4A320D3B24040', '50915631', '', 'A682/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (31, '0105000020E6100000010000000102000000050000003E93FDF33427464076E4A320D3B24040BE22AE5230274640A264CD23DAB240405C751DAA29274640B05582C5E1B240407E7ECE932127464011A1B6B2E9B240406A5A18D819274640BB42C472F0B24040', '50915632', '', 'A862/A1', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (32, '0105000020E61000000100000001020000000D0000005CA49AA3D8264640D25C024B09B2404011312592E8264640C0B2D2A414B24040A46BCB25FA264640A7B5C42522B240402B604C44092746404ED5986B2CB24040E881340818274640385AC46636B24040527DE717252746402B5327FB42B240400F9FCFDB33274640592AB9D452B240408CB5BFB33D274640750C231862B24040969350FA42274640D844662E70B240400AB20A40482746407C60C77F81B2404075BEE9A749274640EB9CB00E91B240400AB20A40482746403EE0CB8E9EB2404035994C7045274640464BD4C1B0B24040', '50915633', '', 'A862/A1', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (33, '0105000020E610000001000000010200000007000000CC704DCB59314640660B523AA2AF40403D5A41785931464087BE164F98AF4040DD5F3DEE5B314640768C2B2E8EAF4040E657738060314640ED15719582AF40405A762DC665314640AA73565579AF40403F2AB4626E3146407016E5886BAF4040034356B77A314640C1024EA555AF4040', '79636530', '', '', 'motorway', 0, 0, 0, 0);
INSERT INTO iraq_roads VALUES (34, '0105000020E61000000100000001020000000600000078915385502746402A8018D7AEB240402562A5DD43274640D9BE36D19DB240404498ECE9342746403575C35B8CB24040F15BBE3FEF264640703DAF1D31B2404076FE486CD22646406A6B44300EB24040A6D24F38BB264640449C983FF0B14040', '82678537', '', 'A862/A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (35, '0105000020E6100000010000000102000000070000004B1DE4F5603146407BA4C16D6DAF4040CFA0A17F82314640E099756B3EAF404065F1ACEEA2314640AA82AC0210AF4040AF850FDBCC3146402E32A605D4AE40401224004922324640983BE93356AE4040CB72C8BC44324640B031F9B028AE404079EEF3CE5732464038C7CA7910AE4040', '224036882', '', 'A86/N11/D383', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (36, '0105000020E61000000100000001020000001200000057FCF03D6D2646405283C4D1B0A94040FBE0C6777326464022DE3AFF76A9404092D5631179264640C6C4419D4DA94040E46B2AE67B2646405C73A2B83EA9404091D26C1E87264640BFD76BD509A94040B4A09C0D9E2646402A1B310E89A840403F373465A7264640D97D22AA4BA84040EFA42A12B8264640B7AE9811DEA740400DC11660C426464034DF1C098FA7404017ED9689C72646408B0CBCA47BA7404020E5CC1BCC264640D8B7EE4163A7404072FAD577D926464040BC53A63DA74040211D1EC2F8264640AF66F8AAF0A64040F76D2D38282746406E0DB6227BA64040380A5A924D274640D63329AA23A64040BF88111D5D274640BA0386F6FBA5404020EEEA55642746402B65BE28E6A5404047E867EA75274640CD6ED2D96EA54040', '224040657', '', 'A86', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (37, '0105000020E6100000010000000102000000120000004850FC18732646403E65EBCF34AA40401A99918B7B26464029E4EF8398AA40403E5E488787264640366964A1E7AA4040322FD16A922646402BC0779B37AB4040B63643609B264640545D1B857FAB40408C69A67B9D26464061777066AAAB40408C69A67B9D2646403B25D698C6AB4040813D26529A26464045C82F7205AC40400227367A90264640706FC8505FAC4040E624EF7783264640BAFC3D67C1AC4040F878324976264640459BE3DC26AD4040C769E3E36E2646405DB6E74361AD40404953F30B6526464012E85D06ADAD40405738EE395526464090BBAD9921AE40404414387E4D26464048E2E5E95CAE4040E706F98F3B2646406E4F90D8EEAE40406A0AAE033126464012E8024D3AAF40400DC9247E20264640B07F8DDAB3AF4040', '224040658', '', 'A86', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (38, '0105000020E610000001000000010200000003000000B6555A9077264640E75C401EB0A940400675DBCF73264640A99D06B1D8A940404850FC18732646403E65EBCF34AA4040', '224040659', '', 'A86', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (39, '0105000020E6100000010000000102000000040000008686C5A86B264640F0C7A30A35AA4040351E11F868264640771101E209AA40406B31D35169264640A5C7A5E0DFA9404057FCF03D6D2646405283C4D1B0A94040', '224040660', '', 'A86', 'motorway', 1, 1, 0, 0);
INSERT INTO iraq_roads VALUES (40, '0105000020E61000000100000001020000000D000000FD474B8A34334640430E000B4FAD4040191241E6143346406B03C12D69AD40403B014D840D334640D9D4D40D6FAD4040FE1E61BDF632464071146A9780AD40406F35A1FFD4324640F24EF4AF9BAD40408712D2BFC9324640F94E2734A4AD404095F7CCEDB932464011C248D4B0AD40400DE9A683AB324640164042DEBCAD404086C0DBCD9D3246400BC91352C8AD4040FEC5223C90324640E64B5E53D6AD4040DC54939680324640A2F14410E7AD4040199B0C7D66324640C864CCB804AE4040C216BB7D563246407CC509021AAE4040', '224040661', '', 'A86/N11/D383', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (41, '0105000020E61000000100000001020000000600000028493206313346405685611B4CAD4040FEB3E6C75F334640B04B9EFC27AD4040DFD1109F8533464043C2F7FE06AD4040A605D440983346409A1139D8F6AC4040AD623B29DD334640B9DEDB99AEAC4040DD15B0D3FE334640966FC7E589AC4040', '224040662', '', 'A86/N11/D383', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (42, '0105000020E6100000010000000102000000060000006D14A3F84228464019EDA7B51FB1404077B92D36522846400CDA50D614B14040E863E3665D284640F758FAD005B140406A40CE458D284640D6A71C93C5B040403F3FE7C990284640CA38A16BBAB04040741E5F8C9228464058F844E8B1B04040', '233575082', '', 'A1', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (43, '0105000020E6100000010000000102000000330000008F447930732C4640C43EA65AB0B04040A30392B06F2C4640F16E1BFCB3B04040223FD12B542C4640D0DCF934DDB04040113235AE242C4640973C9E961FB1404017F5A4A7232C4640A845330521B14040F524FAC6212C4640E8B8BF1F23B14040FAD8B859172C4640E2A2A4D12EB1404047AF06280D2C464089C2781739B1404055940156FD2B4640E98B738A44B140405FD1ADD7F42B4640934D5E0949B14040CD85DBEBEE2B4640F77C282C4CB14040076CBD95DB2B464035DE0CED52B14040002D0208C42B4640DE7F1AAD59B140406FF25B74B22B464089A361E75CB140407DD756A2A22B4640414D88145EB140408CD6F61B922B4640414D88145EB14040C5A2337A7F2B464066B911BB5BB14040089BF001702B4640BB95CA8058B14040E16C29D65F2B46406ABD84AF54B140407F202F5A362B4640D514127A47B1404070E93D3A1A2B4640EC8FE67E3DB1404030A6F4A7E82A4640C5A9D6C22CB140400253173AC02A46400E1714611EB140403C1F5498AD2A4640FEA325451AB14040E923F0879F2A464047FAFE1719B1404062FB24D2912A464070A7BE3D19B1404070E01F00822A4640FEA325451AB1404014D3E011702A4640A9C76C7F1DB1404019C0A5AD5B2A46400C95DAE621B14040C121AF624C2A4640699FD85427B14040FF76D9AF3B2A46407D53FDEF2DB14040774E0EFA2D2A4640AE2E02BE36B14040761C3F541A2A464095E3045C46B1404070F72812022A4640CB3C03345BB140403FD12B54ED294640C2B2E3D06CB14040B8C205EADE29464047E867EA75B14040FBBAC271CF29464043E4F4F57CB1404048ABB58BC429464094BC3AC780B14040C082EAD5B629464051D5A99784B14040385A1F20A92946402C6920F186B14040B1659E019A294640614898B388B140405B43A9BD88294640D8DA560E88B14040680EFF9F792946406296879686B14040A2F4E049662946409488F02F82B14040BDA4315A47294640F1D7648D7AB14040BDAD4F94DF284640E2444F255EB14040D2D4FC42D9284640D069CCDA5CB140402A1B310E89284640E146CA1649B140402EEE505E75284640F63F65A142B14040BF0A4B97592846406918E36833B14040D7E143E44F28464027CD30FF32B14040', '276021340', '', 'A432', 'motorway', 1, 0, 0, 0);
INSERT INTO iraq_roads VALUES (44, '0105000020E61000000100000001020000000300000027ED574B4B2846403333333333B14040DC8FCA0347284640F79E80DC34B1404081D9F3EB3D28464048A5D8D138B14040', '276421023', '', 'A432', 'motorway', 1, 0, 0, 0);


--
-- Name: iraq_roads_ogc_fid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('iraq_roads_ogc_fid_seq', 44, true);


--
-- Name: iraq_roads_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY iraq_roads
    ADD CONSTRAINT iraq_roads_pkey PRIMARY KEY (ogc_fid);


--
-- Name: iraq_roads_geometry_geom_idx; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX iraq_roads_geometry_geom_idx ON iraq_roads USING gist (geometry);


--
-- PostgreSQL database dump complete
--

