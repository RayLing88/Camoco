#!/usr/bin/python3

from Camoco import Camoco
from Locus import Gene,non_overlapping
from Chrom import Chrom
from Genome import Genome

import itertools

class RefGen(Camoco):
    def __init__(self,name,basedir="~/.camoco"):
        # initialize camoco instance
        super().__init__(name,type="RefGen",basedir=basedir)
        self.genome = Genome(
            self.type+self.name,
            chroms = [Chrom(*x) for x in  self.db.cursor().execute(''' 
                SELECT id,length FROM chromosomes
            ''')] 
        )

    def num_genes(self):
        ''' returns the number of genes in the dataset '''
        return self.db.cursor().execute(''' SELECT COUNT(*) FROM genes''').fetchone()[0]

    def from_ids(self,*args,gene_filter=None):
        ''' returns gene object iterable from an iterable of id strings  '''
        if not gene_filter:
            gene_filter = self
        return [ Gene(*x,build=self.build,organism=self.organism) for x in self.db.cursor().execute(''' 
            SELECT chromosome,start,end,strand,id FROM genes WHERE id IN ('{}')
            '''.format("','".join(args))) if Gene(*x) in gene_filter
        ]

    def chromosome(self,id):
        ''' returns a chromosome object '''
        try:
            return Chrom(*self.db.cursor().execute(
                '''SELECT id,length FROM chromosomes WHERE id = ?''',(id,)).fetchone()
            ) 
        except Exception as e:
            self.log("No chromosome where id = {}. Error: {}",id,e)

    def within_gene(self,locus,gene_filter=None):
        ''' returns the gene the locus is within, or None '''
        if not gene_filter:
            gene_filter = self
        try:
            x = [Gene(*x,build=self.build,organism=self.organism) for x in self.db.cursor().execute(''' 
                SELECT chromosome,start,end,strand,id FROM genes 
                WHERE chromosome = ?
                AND start < ?
                AND end > ?
            ''',(locus.chrom,locus.start,locus.start)) if Gene(*x) in gene_filter][0]
            return x
        except Exception as e:
            return None

    def genes_within(self,locus,gene_filter=None):
        ''' Returns the genes within a locus, or None '''
        if not gene_filter:
            gene_filter = self
        try:
            return [Gene(*x,build=self.build,organism=self.organism) for x in self.db.cursor().execute(''' 
                SELECT chromosome,start,end,strand,id FROM genes
                WHERE chromosome = ?
                AND start > ?
                AND end < ?
            ''',(locus.chrom,locus.start,locus.end)) if Gene(*x) in gene_filter]
        except Exception as e:
            return None
        
    def upstream_genes(self,locus,gene_limit=1000,pos_limit=10e6,gene_filter=None):
        ''' returns genes upstream of a locus. Genes are ordered so that the
            nearest genes are at the beginning of the list.'''
        if not gene_filter:
            gene_filter = self
        return [Gene(*x,build=self.build,organism=self.organism) for x in self.db.cursor().execute(''' 
            SELECT chromosome,start,end,strand,id FROM genes
            WHERE chromosome = ?
            AND start < ?
            AND start > ?
            ORDER BY start DESC
            LIMIT ?
            ''',(locus.chrom, locus.start, locus.start - int(pos_limit), 100*int(gene_limit))
        ) if Gene(*x) in gene_filter][0:int(gene_limit)]
    
    def downstream_genes(self,locus,gene_limit=1000,pos_limit=10e6,gene_filter=None):
        ''' returns genes downstream of a locus. Genes are ordered so that the 
            nearest genes are at the beginning of the list. '''
        if not gene_filter:
            gene_filter = self
        return [Gene(*x,build=self.build,organism=self.organism) for x in self.db.cursor().execute(''' 
            SELECT chromosome,start,end,strand,id FROM genes
            WHERE chromosome = ?
            AND start > ?
            AND start < ?
            ORDER BY start ASC
            LIMIT ?
            ''',(locus.chrom, locus.start, locus.start + int(pos_limit), 100*int(gene_limit))
        ) if Gene(*x) in gene_filter][0:int(gene_limit)]


    def flanking_genes(self, locus, gene_limit=2, pos_limit=10e6,chain=True,gene_filter=None):
        ''' Returns genes upstream and downstream from a locus
            ** including genes locus is within **
        '''
        up_genes = self.upstream_genes(locus, gene_limit=gene_limit/2, pos_limit=pos_limit, gene_filter=gene_filter )
        down_genes = self.downstream_genes(locus, gene_limit=gene_limit/2, pos_limit=pos_limit, gene_filter=gene_filter )
        if chain:
            return list(itertools.chain.from_iterable((up_genes,down_genes)))
        else:
            return (up_genes,down_genes)

    def candidate_genes(self, locus, gene_limit=2, pos_limit=10e6,chain=True,gene_filter=None):
        ''' if locus is within gene, returns that gene, 
            otherwise returns flanking genes '''
        if not gene_filter:
            gene_filter = self
        within = self.within_gene(locus,gene_filter=gene_filter)
        if not within:
            return self.flanking_genes(
                locus,gene_limit,pos_limit,chain=chain,gene_filter=gene_filter
            )
        else:
            return [within] # candidate genes as in plural, return iteratable

    def nearest_gene(self,locus,gene_filter=None):
        ''' return the gene nearest the locus '''
        if not gene_filter:
            gene_filter = self
        candidates = self.flanking_genes(locus,gene_filter=gene_filter)
        val,idx  = min((val,idx) for (idx,val) in enumerate([abs(locus-candidate) for candidate in candidates]))
        return candidates[idx]

    def bootstrap_genes(self, gene_list, gene_filter = None):
        ''' returns a random set of non overlapping genes as larges as 
            the gene list passed in '''
        if not gene_filter:
            gene_filter = self
        bootstrap = [ self.nearest_gene(self.genome.rSNP(),gene_filter=gene_filter) for gene in gene_list ]
        if non_overlapping(bootstrap):
            return bootstrap
        else:
            return self.bootstrap_genes(gene_list,gene_filter=gene_filter)

    def bootstrap_flanking_genes(self,locus,gene_limit=4,pos_limit=50000,gene_filter=None):
        ''' Returns a randoms set of non overlapping flanking genes calculated from 
            SNPs flanking genes which is the same number of genes as would be calculated
            from the actual flanking genes from SNP list'''
        num_genes = len(self.flanking_genes(locus,gene_limit,pos_limit,gene_filter=gene_filter))
        while True:
            bootstrapped = self.flanking_genes(
                self.genome.rSNP(),
                gene_limit,
                pos_limit,
                gene_filter=gene_filter
            )
            if len(bootstrapped) == num_genes:
                return bootstrapped
           
    def summary(self): 
        return ("\n".join([
            'Reference Genome: {} - {} - {}',
            '{} genes',
            'Genome:',
            '{}']).format(self.organism,self.build,self.name,self.num_genes(),self.genome))

    def __repr__(self):
        return 'Reference Genome: {} - {} - {}'.format(self.organism,self.build,self.name)

    def __contains__(self,obj):
        ''' flexible on what you pass into the 'in' function '''
        try:
            # you can pass in a gene object (this should ALWAYS be true if you 
            # created gene object from this RefGen)
            if self.db.cursor().execute('''
                SELECT COUNT(*) FROM genes WHERE id = ?''',(obj.id,)).fetchone()[0] == 1:
                return True
            else:
                return False
        except Exception as e:
            pass
        try:
            # Can be a string object
            if self.db.cursor().execute('''
                SELECT COUNT(*) FROM genes WHERE id = ?''',(str(obj),)).fetchone()[0] == 1:
                return True
            else:
                return False
        except Exception as e:
            pass
        self.log("object {} not correct type to test membership in {}",obj,self.name)


class RefGenBuilder(Camoco):
    def __init__(self,name,description,build,organism,basedir="~/.camoco"):
        # Initiate CAmoco instance
        super().__init__(name,description=description,type="RefGen",basedir=basedir)
        self._create_tables()
        # Set the table globals
        self._global('build',build)
        self._global('organism',organism)

    def _build_indices(self):
        cur = self.db.cursor()
        cur.execute('''
            CREATE INDEX IF NOT EXISTS genepos ON genes (chromosome,start);
            CREATE INDEX IF NOT EXISTS geneid ON genes (id);
        ''')
    def add_gene(self,id,chromosome,start,end,strand):
        self.db.cursor().execute(''' 
            INSERT OR IGNORE INTO genes VALUES (?,?,?,?,?)
        ''',(id,chromosome,start,end,strand))

    def add_chromosome(self,chrom):
        ''' adds a chromosome object to the class '''
        self.db.cursor().execute('''
            INSERT OR REPLACE INTO chromosomes VALUES (?,?)
        ''',(chrom.id,chrom.length))

    def import_from_txt(self,filename,sep="\t"):
        ''' assumes columns are in the order: id, chromosome, start, end, strand ''' 
        genes = []
        with open(filename,'r') as TXT:
            for line in TXT:
                fields = line.strip().split("\t")
                genes.append(fields)
        cur = self.db.cursor()
        cur.execute('BEGIN TRANSACTION')
        cur.executemany('''INSERT INTO genes (id,chromosome,start,end,strand) 
            VALUES (?,?,?,?,?)''',genes)
        cur.execute('END TRANSACTION')

    def import_from_fasta(self,filename):
        pass
       
    def _create_tables(self):
        cur = self.db.cursor()
        cur.execute("PRAGMA page_size = 1024;")
        cur.execute("PRAGMA cache_size = 100000;")
        cur.execute(''' 
            CREATE TABLE IF NOT EXISTS chromosomes (
                id TEXT NOT NULL UNIQUE,
                length INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS genes (
                id TEXT NOT NULL,
                chromosome TEXT NOT NULL,
                start INTEGER,
                end INTEGER,
                strand INTEGER
            );
        ''');

